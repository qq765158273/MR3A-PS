"""Translate MaaFramework controller operations to the browser display."""

import ctypes
import hashlib
import logging
from typing import Callable

import numpy as np
from maa.buffer import ImageBuffer
from maa.controller import CustomController, MaaCustomControllerCallbacks
from maa.define import MaaControllerFeatureEnum
from playwright.sync_api import Page

from .config import Config
from .imaging import png_to_bgr
from .keymap import vk_to_key
from .native_canvas import capture_native, inspect_canvas, native_point
from .session import BrowserSession, display, open_remote

log = logging.getLogger(__name__)


class JumpServerController(CustomController):
    def __init__(self, session: BrowserSession, cfg: Config):
        self.session = session
        self.cfg = cfg
        super().__init__()

    @property
    def c_handle(self):
        # The 5.12.2 Python binding otherwise lets screencap exceptions escape a ctypes callback.
        self._callbacks.screencap = self._safe_screencap
        return super().c_handle

    @staticmethod
    @MaaCustomControllerCallbacks.ScreencapFunc
    def _safe_screencap(trans_arg, image_buffer) -> int:
        if not trans_arg:
            return 0
        try:
            controller = ctypes.cast(trans_arg, ctypes.py_object).value
            return int(ImageBuffer(image_buffer).set(controller.screencap()))
        except Exception:
            log.exception("Controller screenshot failed")
            return 0

    def connect(self) -> bool:
        return self._run(lambda page: display(page, self.cfg).is_visible())

    def connected(self) -> bool:
        return self._run(lambda page: not page.is_closed() and display(page, self.cfg).is_visible())

    def request_uuid(self) -> str:
        digest = hashlib.sha256(self.cfg.connect_url.encode("utf-8")).hexdigest()
        return f"jumpserver:{digest}"

    def get_features(self) -> int:
        return MaaControllerFeatureEnum.Null

    def start_app(self, intent: str) -> bool:
        return False

    def stop_app(self, intent: str) -> bool:
        return False

    def screencap(self) -> np.ndarray:
        if self.cfg.capture_mode == "native_canvas":
            return self.session.call(lambda page: capture_native(page, self.cfg))
        if self.cfg.capture_mode != "viewport":
            raise ValueError(f"Unsupported capture mode: {self.cfg.capture_mode}")
        return png_to_bgr(self.session.call(lambda page: display(page, self.cfg).screenshot()))

    def click(self, x: int, y: int) -> bool:
        def perform(page: Page) -> bool:
            px, py = self._point(page, x, y)
            page.mouse.click(px, py)
            return True
        return self._run(perform)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int) -> bool:
        def perform(page: Page) -> bool:
            px1, py1 = self._point(page, x1, y1)
            px2, py2 = self._point(page, x2, y2)
            steps = max(1, duration // 20)
            page.mouse.move(px1, py1)
            page.mouse.down()
            try:
                for step in range(1, steps + 1):
                    page.mouse.move(px1 + (px2 - px1) * step / steps,
                                    py1 + (py2 - py1) * step / steps)
                    if duration > 0:
                        page.wait_for_timeout(duration / steps)
            finally:
                page.mouse.up()
            return True
        return self._run(perform)

    def touch_down(self, contact: int, x: int, y: int, pressure: int) -> bool:
        return False

    def touch_move(self, contact: int, x: int, y: int, pressure: int) -> bool:
        return False

    def touch_up(self, contact: int) -> bool:
        return False

    def click_key(self, keycode: int) -> bool:
        return self._run(lambda page: page.keyboard.press(vk_to_key(keycode)) or True)

    def input_text(self, text: str) -> bool:
        return self._run(lambda page: page.keyboard.type(text) or True)

    def key_down(self, keycode: int) -> bool:
        return self._run(lambda page: page.keyboard.down(vk_to_key(keycode)) or True)

    def key_up(self, keycode: int) -> bool:
        return self._run(lambda page: page.keyboard.up(vk_to_key(keycode)) or True)

    def press_combo(self, keys: list[str]) -> bool:
        return self._run(lambda page: page.keyboard.press("+".join(keys)) or True)

    def _point(self, page: Page, x: int, y: int) -> tuple[float, float]:
        if self.cfg.capture_mode == "native_canvas":
            return native_point(page, self.cfg, x, y)
        if self.cfg.capture_mode != "viewport":
            raise ValueError(f"Unsupported capture mode: {self.cfg.capture_mode}")
        box = display(page, self.cfg).bounding_box()
        if box is None:
            raise RuntimeError("Remote display is not visible")
        if not (0 <= x < box["width"] and 0 <= y < box["height"]):
            raise ValueError(f"Point ({x}, {y}) is outside the remote display")
        return box["x"] + x, box["y"] + y

    def _run(self, fn: Callable[[Page], bool]) -> bool:
        try:
            def perform(page: Page) -> bool:
                if self.cfg.capture_mode == "native_canvas":
                    inspect_canvas(page, self.cfg)
                return fn(page)
            return bool(self.session.call(perform))
        except Exception:
            log.exception("Controller operation failed")
            return False


def connect_controller(cfg: Config) -> tuple[BrowserSession, JumpServerController]:
    if cfg.connection_mode == "cli":
        from .cli_controller import connect_cli_controller
        return connect_cli_controller(cfg)
    if cfg.connection_mode != "launch":
        raise ValueError(f"Unsupported connection mode: {cfg.connection_mode}")
    session = BrowserSession(cfg)
    session.start()
    try:
        open_remote(session, cfg)
        controller = JumpServerController(session, cfg)
        if not controller.set_screenshot_use_raw_size(True):
            raise RuntimeError("Failed to enable raw-size screenshots")
        if not controller.post_connection().wait().succeeded:
            raise RuntimeError("Maa controller connection failed")
        return session, controller
    except BaseException:
        session.stop()
        raise
