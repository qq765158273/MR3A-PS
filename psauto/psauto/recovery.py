"""Browser screenshot/input channel for the native Maa idle-timeout pipeline.

This channel pads the browser viewport to 1920x1080 without rescaling pixels.
It exists because JumpServer removes that canvas after disconnecting. OCR,
templates, waits and decisions belong to the resource pipeline, not this module.
"""

import base64
import json
from urllib.parse import urlsplit

import numpy as np

from .cli_controller import CliController, PlaywrightCliSession
from .imaging import png_to_bgr


BROWSER_WIDTH = 1920
BROWSER_HEIGHT = 1080

_BROWSER_BODY = """async (page) => {
  const request = __REQUEST__;
  if (new URL(page.url()).origin !== request.origin)
    throw new Error('Recovery page is outside the configured JumpServer origin');
  const size = await page.evaluate(() => ({width: innerWidth, height: innerHeight}));
  if (size.width !== request.width || size.height < 720 || size.height > request.height)
    throw new Error('Browser viewport differs from the recovery screenshot baseline');
  if (request.operation === 'inspect') return true;
  if (request.operation === 'screencap') {
    const png = (await page.screenshot({animations: 'disabled'})).toString('base64');
    const after = await page.evaluate(() => ({width: innerWidth, height: innerHeight}));
    if (size.width !== after.width || size.height !== after.height)
      throw new Error('Browser viewport changed while capturing');
    return {png, ...size};
  }
  if (request.operation === 'click') {
    const {x, y} = request;
    if (!request.viewport || size.width !== request.viewport.width || size.height !== request.viewport.height)
      throw new Error('Browser viewport changed after the recognition screenshot');
    if (!Number.isInteger(x) || !Number.isInteger(y) || x < 0 || y < 0 ||
        x >= size.width || y >= size.height) throw new Error('Recovery click outside viewport');
    await page.mouse.click(x, y);
    return true;
  }
  throw new Error('Recovery channel only supports screenshots and clicks');
}"""


class BrowserRecoverySession(PlaywrightCliSession):
    viewport = None

    def request(self, operation, **params):
        if operation == 'reconnect':
            self.request('inspect')
            result = self.invoke_cli(['reload'], raw=False)
            if result.returncode:
                raise RuntimeError('CLI reload failed; recovery stopped')
            if '### Modal state' in result.stdout:
                modal = result.stdout.split('### Modal state', 1)[1].split('### ', 1)[0]
                if modal.count('dialog with message') != 1 or '"beforeunload" dialog with message' not in modal:
                    raise RuntimeError('Unexpected browser dialog; recovery stopped')
                accepted = self.invoke_cli(['dialog-accept'], raw=False)
                if accepted.returncode:
                    raise RuntimeError('Unable to accept the reload confirmation')
            self.viewport = None
            return True
        parsed = urlsplit(self.cfg.jumpserver_url)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError('Recovery requires a valid JumpServer origin')
        request = {"operation": operation, "frame": self.cfg.display_frame,
                   "origin": f'{parsed.scheme}://{parsed.netloc}', "viewport": self.viewport,
                   "width": BROWSER_WIDTH, "height": BROWSER_HEIGHT, **params}
        result = self.run_code(_BROWSER_BODY.replace('__REQUEST__', json.dumps(request)))
        if operation == 'screencap':
            self.viewport = {"width": result['width'], "height": result['height']}
        return result


class BrowserRecoveryController(CliController):
    def start_app(self, intent):
        if intent != 'jumpserver:reconnect':
            return False
        return self._dispatch('reconnect')

    def screencap(self):
        result = self.session.request('screencap')
        image = png_to_bgr(base64.b64decode(result['png'], validate=True))
        if image.shape != (result['height'], result['width'], 3):
            raise RuntimeError('Browser screenshot differs from recovery baseline')
        padded = np.full((BROWSER_HEIGHT, BROWSER_WIDTH, 3), 255, dtype=np.uint8)
        padded[:image.shape[0], :image.shape[1]] = image
        return padded


def connect_recovery_controller(cfg):
    session = BrowserRecoverySession(cfg)
    controller = BrowserRecoveryController(session, cfg)
    if not controller.set_screenshot_use_raw_size(True) or not controller.post_connection().wait().succeeded:
        raise RuntimeError('Unable to initialize the browser recovery controller')
    return session, controller
