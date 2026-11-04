"""Maa controller for a pre-authorized Playwright CLI browser session."""

import hashlib
import json
import logging
import queue
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time

from .controller import JumpServerController
from .keymap import vk_to_key
from .native_canvas import _INSPECT, decode_canvas

log = logging.getLogger(__name__)


class PlaywrightCliSession:
    def __init__(self, cfg):
        self.cfg = cfg
        self.poisoned = False
        self._worker = None
        self._responses = queue.Queue()
        self._request_lock = threading.Lock()
        self._request_id = 0
        self.timings = []
        self.node = shutil.which("node")
        self.script = cfg.resolve_path(cfg.cli_script)
        if not self.node or not self.script.is_file():
            raise RuntimeError("Node.js or the configured Playwright CLI script is missing")
        if cfg.capture_mode != "native_canvas":
            raise ValueError("CLI connection requires native_canvas capture mode")
        if not cfg.display_selector:
            raise ValueError("display_selector is required")
        self.cwd = cfg.resolve_path(cfg.cli_workdir)
        if not self.cwd.is_dir():
            raise RuntimeError("The configured CLI working directory does not exist")

    def request(self, operation, **params):
        if self.poisoned:
            raise RuntimeError("CLI session is disabled after a timeout; inspect the remote screen before restarting")
        request = {"operation": operation, "frame": self.cfg.display_frame,
                   "selector": self.cfg.display_selector, "width": self.cfg.remote_width,
                   "height": self.cfg.remote_height,
                   "clipboard_required": self.cfg.text_input_mode == 'clipboard', **params}
        code = _CLI_BODY.replace("__INSPECT__", _INSPECT).replace("__REQUEST__", json.dumps(request))
        started = time.perf_counter()
        try:
            return self.run_code(code)
        finally:
            self.timings.append({'operation': operation,
                                 'elapsed_ms': round((time.perf_counter() - started) * 1000, 2)})

    def run_code(self, code):
        """Execute transport code in the existing CLI session without opening a browser."""
        if self.poisoned:
            raise RuntimeError("CLI session is disabled after a timeout; inspect the remote screen before restarting")
        filename = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".js",
                                             prefix="psauto-cli-", dir=self.cwd, delete=False) as script:
                filename = Path(script.name)
                script.write(code)
            result = self.invoke_cli(['run-code', f'--filename={filename}'])
        finally:
            if filename is not None:
                filename.unlink(missing_ok=True)
        if result.returncode != 0:
            details = (result.stdout + '\n' + result.stderr).strip()
            error_file = self.cfg.resolve_path('debug/cli-last-error.txt')
            error_file.parent.mkdir(parents=True, exist_ok=True)
            error_file.write_text(details[:16384], encoding='utf-8')
            first_line = next((line for line in details.splitlines() if line and not line.startswith('### ')), '')
            first_line = re.sub(r'https?://\S+', '[URL]', first_line)
            raise RuntimeError(f"Playwright CLI operation failed (exit {result.returncode}): {first_line[:300]}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Playwright CLI returned an invalid response") from exc

    def invoke_cli(self, arguments, raw=True):
        """Transport a structured CLI command; callers must not log its browser metadata."""
        if self.poisoned:
            raise RuntimeError('CLI session is disabled after a timeout')
        if self.cfg.cli_persistent_client:
            with self._request_lock:
                if self._worker is None:
                    self._start_worker()
                self._request_id += 1
                request_id = self._request_id
                try:
                    self._worker.stdin.write(json.dumps({'id': request_id, 'arguments': list(arguments),
                                                         'raw': raw}) + '\n')
                    self._worker.stdin.flush()
                    response = self._read_response()
                    if response.get('id') != request_id:
                        raise RuntimeError('CLI client returned an unexpected response')
                    return subprocess.CompletedProcess(arguments, response['returncode'],
                                                       response['stdout'], response['stderr'])
                except (BrokenPipeError, OSError, RuntimeError):
                    # A broken client may already have submitted an action. Never replay it.
                    self.poisoned = True
                    self._stop_worker()
                    raise
        command = [self.node, str(self.script), f'-s={self.cfg.cli_session}']
        if raw:
            command.append('--raw')
        try:
            return subprocess.run(command + list(arguments), cwd=self.cwd, capture_output=True,
                                  encoding='utf-8', errors='replace', timeout=45,
                                  creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except subprocess.TimeoutExpired as exc:
            self.poisoned = True
            raise TimeoutError('CLI operation timed out and may still be running') from exc

    def stop(self):
        # Stop only our client. The browser and the CLI daemon are owned by the user.
        self._stop_worker()

    def _start_worker(self):
        helper = Path(__file__).with_name('cli_worker.cjs')
        self._responses = queue.Queue()
        self._worker = subprocess.Popen([self.node, str(helper), str(self.script.resolve()), self.cfg.cli_session],
                                        cwd=self.cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        worker, responses = self._worker, self._responses
        def read():
            try:
                for line in worker.stdout:
                    responses.put(json.loads(line))
            except (ValueError, OSError):
                pass
            finally:
                responses.put({'fatal': 'Playwright CLI client closed unexpectedly'})
        threading.Thread(target=read, daemon=True, name='psauto-cli-output').start()
        try:
            response = self._read_response()
        except Exception:
            self._stop_worker()
            raise
        if response.get('ready') is not True:
            self._stop_worker()
            raise RuntimeError(response.get('fatal', 'CLI client could not start'))

    def _read_response(self):
        try:
            response = self._responses.get(timeout=45)
        except queue.Empty as exc:
            self.poisoned = True
            self._stop_worker()
            raise TimeoutError('CLI operation timed out and may still be running') from exc
        if 'fatal' in response:
            raise RuntimeError(response['fatal'])
        return response

    def _stop_worker(self):
        worker, self._worker = self._worker, None
        if worker is None:
            return
        try:
            worker.stdin.close()
            worker.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            worker.kill()
            worker.wait(timeout=5)
        finally:
            worker.stdout.close()


_CLI_BODY = """async (page) => {
  const request = __REQUEST__;
  if (request.operation === 'key_up') {
    await page.keyboard.up(request.key);
    return true;
  }
  const inspect = __INSPECT__;
  const root = request.frame ? page.frameLocator(request.frame).locator(request.selector).first()
                             : page.locator(request.selector).first();
  const transport = await root.count() ? await root.evaluate(el => {
    const buttons = [...el.ownerDocument.querySelectorAll('button')]
      .filter(button => button.textContent.trim() === '\\u526a\\u8d34\\u677f');
    let component = buttons[0]?.__vue__;
    while (component && component.$options?.name !== 'GuacamoleConnect') component = component.$parent;
    return {has_display: true, known: !!component,
      tunnel_state: component?.tunnel?.state ?? null,
      client_state: component?.clientState ?? null,
      clipboard_ready: buttons.length === 1 && !buttons[0].disabled};
  }) : {has_display: false, known: false, clipboard_ready: false};
  if (request.operation === 'transport_state') return transport;
  if (!transport.has_display) throw new Error('Remote display is unavailable');
  // A closed tunnel can leave a perfectly recognizable last frame on the canvas.
  // clientState can also remain "Connected" after closure; require the live tunnel.
  if (transport.known && (transport.tunnel_state !== 1 || transport.client_state !== 'Connected'))
    throw new Error('RDP transport is not connected; cached canvas is not a live screenshot');
  if (request.clipboard_required && !transport.clipboard_ready)
    throw new Error('JumpServer clipboard channel is unavailable');
  if (request.operation === 'screencap' && await page.evaluate(() => document.visibilityState === 'hidden')) {
    // Hidden Chrome can defer Guacamole's drawing callbacks. Flush a browser
    // frame first, then read the native canvas without scaling its pixels.
    await page.screenshot({animations: 'disabled'});
  }
  const info = await root.evaluate(inspect, request.operation === 'screencap');
  if (info.width !== request.width || info.height !== request.height)
    throw new Error(`Remote desktop is ${info.width}x${info.height}, expected ${request.width}x${request.height}`);
  if (info.bitmapWidth < info.width || info.bitmapHeight < info.height || info.cssWidth <= 0 || info.cssHeight <= 0)
    throw new Error('Invalid canvas dimensions');
  if (request.operation === 'screencap') return info;
  if (request.operation === 'inspect') {
    if (request.prepare) {
      await page.screenshot({animations: 'disabled'});
      const sink = root.locator('textarea');
      if (await sink.count() !== 1) throw new Error('Expected one remote keyboard input sink');
      await sink.focus();
    }
    return true;
  }
  if (['key', 'key_down', 'input_text'].includes(request.operation)) {
    const keyboardReady = await root.evaluate(el => {
      const active = el.ownerDocument.activeElement;
      return !!active && el.contains(active);
    });
    if (!keyboardReady) throw new Error('Remote display does not have keyboard focus');
  }
  const point = async (x, y) => {
    if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0 || x >= request.width || y >= request.height)
      throw new Error('Point is outside the remote desktop');
    const canvas = root.locator('canvas').nth(info.canvasIndex);
    const box = await canvas.boundingBox(), clip = await root.boundingBox();
    if (!box || !clip) throw new Error('Remote display is not visible');
    const px = box.x + x * box.width / info.bitmapWidth, py = box.y + y * box.height / info.bitmapHeight;
    const viewport = await page.evaluate(() => ({width: innerWidth, height: innerHeight}));
    if (px < clip.x || py < clip.y || px >= clip.x + clip.width || py >= clip.y + clip.height ||
        px < 0 || py < 0 || px >= viewport.width || py >= viewport.height)
      throw new Error('Point is clipped or outside the browser viewport');
    const reachable = await canvas.evaluate((el, p) => {
      const r = el.getBoundingClientRect();
      const hit = document.elementFromPoint(r.x + p.x * r.width / el.width, r.y + p.y * r.height / el.height);
      return !!hit && (hit === el || (hit.contains(el) && el.parentElement.contains(hit)));
    }, {x, y});
    if (!reachable) throw new Error('Remote point is obscured or clipped');
    if (request.frame && !await page.locator(request.frame).first().evaluate(
        (frame, p) => document.elementFromPoint(p.x, p.y) === frame, {x:px, y:py}))
      throw new Error('Remote frame is obscured');
    return {x:px, y:py};
  };
  if (request.operation === 'click') {
    const p = await point(request.x, request.y);
    await page.mouse.click(p.x, p.y);
  } else if (request.operation === 'swipe') {
    const start = await point(request.x1, request.y1);
    await point(request.x2, request.y2);
    await page.mouse.move(start.x, start.y);
    await page.mouse.down();
    try {
      const steps = Math.max(1, Math.ceil(request.duration / 50));
      for (let i = 1; i <= steps; i++) {
        const current = await root.evaluate(inspect, false);
        if (current.width !== request.width || current.height !== request.height ||
            current.bitmapWidth !== info.bitmapWidth || current.bitmapHeight !== info.bitmapHeight)
          throw new Error('Remote dimensions changed during swipe');
        const p = await point(Math.round(request.x1 + (request.x2-request.x1)*i/steps),
                              Math.round(request.y1 + (request.y2-request.y1)*i/steps));
        await page.mouse.move(p.x, p.y);
        if (request.duration > 0) await page.waitForTimeout(request.duration / steps);
      }
    } finally { await page.mouse.up(); }
  } else if (request.operation === 'key') {
    try { await page.keyboard.press(request.key); }
    finally {
      for (const modifier of request.key.split('+').slice(0, -1))
        await page.keyboard.up(modifier);
    }
  } else if (request.operation === 'key_down') {
    await page.keyboard.down(request.key);
  } else if (request.operation === 'input_text') {
    if (request.clipboard) {
      if (!request.frame) throw new Error('JumpServer clipboard input requires the configured remote iframe');
      const frame = page.frameLocator(request.frame);
      // These are browser utility controls, not PSIDE controls. Activate their DOM handlers
      // directly so background/minimized Chrome does not need animation frames or OS focus.
      const activateUtility = async button => button.evaluate(el => {
        if (el.tagName !== 'BUTTON' || el.disabled) throw new Error('Clipboard utility button is unavailable');
        el.click();
      });
      const clipboardButton = frame.locator('button').filter({hasText: '\u526a\u8d34\u677f'});
      if (await clipboardButton.count() !== 1)
        throw new Error('Expected one JumpServer clipboard toolbar button');
      const closeSettings = async () => frame.locator('.background').evaluateAll(es => {
        const open = es.filter(el => el.parentElement.classList.contains('show'));
        if (open.length > 1) throw new Error('Ambiguous JumpServer settings overlays');
        for (const mask of open) mask.click();
      });
      const closeClipboard = frame.locator('button[aria-label="close \u526a\u8d34\u677f"]');
      let openedClipboard = false;
      try {
        await closeSettings();
        // The clipboard button's handler is available while its toolbar is collapsed.
        await activateUtility(clipboardButton); openedClipboard = true;
        const clipboard = frame.locator('.el-drawer textarea.el-textarea__inner');
        if (await clipboard.count() !== 1) throw new Error('Expected one JumpServer clipboard textbox');
        await clipboard.fill(request.text, {timeout: 5000});
        if ((await clipboard.inputValue()).replace(/\\r\\n/g, '\\n') !== request.text.replace(/\\r\\n/g, '\\n'))
          throw new Error('Clipboard textbox did not accept the payload');
        await clipboard.blur();
        await page.waitForTimeout(1000);
        await activateUtility(closeClipboard); openedClipboard = false;
        await closeSettings();
        // Finish the drawer's leaving transition even when Chrome is hidden.
        // The original canvas alone cannot reveal this browser-side overlay.
        await page.screenshot({animations: 'disabled'});
        await frame.locator('.el-drawer__wrapper.clipboardDrawer').waitFor({state: 'hidden', timeout: 3000});
        const after = await root.evaluate(inspect, false);
        if (after.width !== request.width || after.height !== request.height)
          throw new Error('Remote dimensions changed while preparing clipboard input');
        const sink = root.locator('textarea');
        if (await sink.count() !== 1) throw new Error('Expected one remote keyboard input sink');
        await sink.focus();
        if (!await root.evaluate(el => el.contains(el.ownerDocument.activeElement)))
          throw new Error('Remote keyboard focus was not restored after clipboard input');
        await page.keyboard.press('Control+v');
      } finally {
        if (openedClipboard) await activateUtility(closeClipboard).catch(() => {});
        await closeSettings().catch(() => {});
        await root.locator('textarea').focus({timeout: 1000}).catch(() => {});
      }
    } else {
      await page.keyboard.type(request.text);
    }
  } else {
    throw new Error('Unsupported operation');
  }
  return true;
}"""


class CliController(JumpServerController):
    def __init__(self, session, cfg):
        self._held_keys = set()
        super().__init__(session, cfg)

    def request_uuid(self):
        digest = hashlib.sha256(self.cfg.cli_session.encode("utf-8")).hexdigest()
        return f"playwright-cli:{digest}"

    def _dispatch(self, operation, **params):
        try:
            return bool(self.session.request(operation, **params))
        except Exception:
            log.exception("Playwright CLI controller operation failed")
            return False

    def connect(self):
        return self._dispatch("inspect", prepare=self.cfg.text_input_mode == 'clipboard')

    def connected(self):
        return self._dispatch("inspect")

    def screencap(self):
        try:
            return decode_canvas(self.session.request("screencap"), self.cfg)
        except Exception:
            self._release_held_keys()
            raise

    def click(self, x, y):
        return self._dispatch("click", x=x, y=y)

    def swipe(self, x1, y1, x2, y2, duration):
        if not 0 <= duration <= 10000:
            log.error("Swipe duration must be between 0 and 10000 ms")
            return False
        return self._dispatch("swipe", x1=x1, y1=y1, x2=x2, y2=y2, duration=duration)

    def click_key(self, keycode):
        try:
            success = self._dispatch("key", key=vk_to_key(keycode))
        except KeyError:
            success = False
        if not success:
            self._release_held_keys()
        return success

    def key_down(self, keycode):
        try:
            key = vk_to_key(keycode)
        except KeyError:
            return False
        self._held_keys.add(key)
        if self._dispatch("key_down", key=key):
            return True
        self._release_held_keys()
        return False

    def key_up(self, keycode):
        try:
            key = vk_to_key(keycode)
        except KeyError:
            return False
        if self._dispatch("key_up", key=key):
            self._held_keys.discard(key)
            return True
        self._release_held_keys()
        return False

    def _release_held_keys(self):
        for key in tuple(self._held_keys):
            try:
                if self.session.request("key_up", key=key):
                    self._held_keys.discard(key)
            except Exception:
                log.exception("Failed to release held key after a controller error")

    def press_combo(self, keys):
        return self._dispatch("key", key="+".join(keys))

    def input_text(self, text):
        if self.cfg.text_input_mode not in ('keyboard', 'clipboard'):
            log.error('Unsupported text input mode')
            return False
        if not isinstance(text, str) or '\x00' in text or len(text.encode('utf-8')) > 65536:
            log.error('Text payload is invalid or exceeds 64 KiB')
            return False
        return self._dispatch("input_text", text=text, clipboard=self.cfg.text_input_mode == 'clipboard')


def connect_cli_controller(cfg):
    session = PlaywrightCliSession(cfg)
    controller = CliController(session, cfg)
    if not controller.set_screenshot_use_raw_size(True) or not controller.post_connection().wait().succeeded:
        session.stop()
        raise RuntimeError("Maa CLI controller connection failed")
    return session, controller
