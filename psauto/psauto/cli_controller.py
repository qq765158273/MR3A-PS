"""Maa controller for a pre-authorized Playwright CLI browser session."""

import hashlib
import json
import logging
from pathlib import Path
import shutil
import subprocess
import tempfile

from .controller import JumpServerController
from .keymap import vk_to_key
from .native_canvas import _INSPECT, decode_canvas

log = logging.getLogger(__name__)


class PlaywrightCliSession:
    def __init__(self, cfg):
        self.cfg = cfg
        self.poisoned = False
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
                   "height": self.cfg.remote_height, **params}
        code = _CLI_BODY.replace("__INSPECT__", _INSPECT).replace("__REQUEST__", json.dumps(request))
        filename = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".js",
                                             prefix="psauto-cli-", dir=self.cwd, delete=False) as script:
                filename = Path(script.name)
                script.write(code)
            try:
                result = subprocess.run([self.node, str(self.script), f"-s={self.cfg.cli_session}",
                                         "--raw", "run-code", f"--filename={filename}"], cwd=self.cwd,
                                        capture_output=True, encoding="utf-8", errors="replace", timeout=45)
            except subprocess.TimeoutExpired as exc:
                self.poisoned = True
                raise TimeoutError("CLI operation timed out and may still be running") from exc
        finally:
            if filename is not None:
                filename.unlink(missing_ok=True)
        if result.returncode != 0:
            raise RuntimeError(f"Playwright CLI operation failed (exit {result.returncode}): {result.stderr.strip()[:500]}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Playwright CLI returned an invalid response") from exc

    def stop(self):
        # The attached browser and CLI session are owned by the user.
        pass


_CLI_BODY = """async (page) => {
  const request = __REQUEST__;
  if (request.operation === 'key_up') {
    await page.keyboard.up(request.key);
    return true;
  }
  const inspect = __INSPECT__;
  const root = request.frame ? page.frameLocator(request.frame).locator(request.selector).first()
                             : page.locator(request.selector).first();
  const info = await root.evaluate(inspect, request.operation === 'screencap');
  if (info.width !== request.width || info.height !== request.height)
    throw new Error(`Remote desktop is ${info.width}x${info.height}, expected ${request.width}x${request.height}`);
  if (info.bitmapWidth < info.width || info.bitmapHeight < info.height || info.cssWidth <= 0 || info.cssHeight <= 0)
    throw new Error('Invalid canvas dimensions');
  if (request.operation === 'screencap') return info;
  if (request.operation === 'inspect') return true;
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
    const canvas = root.locator('canvas');
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
    await page.keyboard.press(request.key);
  } else if (request.operation === 'key_down') {
    await page.keyboard.down(request.key);
  } else if (request.operation === 'input_text') {
    await page.keyboard.type(request.text);
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
        return self._dispatch("inspect")

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
        return self._dispatch("input_text", text=text)


def connect_cli_controller(cfg):
    session = PlaywrightCliSession(cfg)
    controller = CliController(session, cfg)
    if not controller.set_screenshot_use_raw_size(True) or not controller.post_connection().wait().succeeded:
        raise RuntimeError("Maa CLI controller connection failed")
    return session, controller
