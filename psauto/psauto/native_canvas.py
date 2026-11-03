"""Read a single Guacamole canvas and map native pixels to page coordinates."""

import base64
import io
import math

import numpy as np
from PIL import Image
from playwright.sync_api import Page

from .config import Config
from .session import display


# Guacamole may pad the canvas allocation; the parent's client size is the desktop size.
_INSPECT = """(root, capture) => {
  const canvases = root.querySelectorAll('canvas');
  if (canvases.length !== 1) throw new Error(`Expected one canvas, found ${canvases.length}`);
  const canvas = canvases[0], surface = canvas.parentElement;
  if (!surface) throw new Error('Canvas surface is missing');
  for (let el = canvas; el; el = el.parentElement) {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility !== 'visible' || Number(style.opacity) !== 1)
      throw new Error('Canvas or ancestor is hidden or transparent');
    if (style.transform !== 'none') {
      const m = new DOMMatrixReadOnly(style.transform);
      if (!m.is2D || Math.abs(m.b) > 1e-7 || Math.abs(m.c) > 1e-7 || m.a <= 0 || m.d <= 0)
        throw new Error('Unsupported canvas transform');
    }
  }
  const rect = canvas.getBoundingClientRect();
  return {width: surface.clientWidth, height: surface.clientHeight,
    bitmapWidth: canvas.width, bitmapHeight: canvas.height,
    cssWidth: rect.width, cssHeight: rect.height,
    data: capture ? canvas.toDataURL('image/png') : null};
}"""


def inspect_canvas(page: Page, cfg: Config, capture: bool = False) -> dict:
    info = display(page, cfg).evaluate(_INSPECT, capture)
    width, height = info["width"], info["height"]
    if (width, height) != (cfg.remote_width, cfg.remote_height):
        raise RuntimeError(f"Remote desktop is {width}x{height}, expected {cfg.remote_width}x{cfg.remote_height}")
    if info["bitmapWidth"] < width or info["bitmapHeight"] < height:
        raise RuntimeError("Canvas buffer is smaller than the remote desktop")
    if info["cssWidth"] <= 0 or info["cssHeight"] <= 0:
        raise RuntimeError("Remote canvas has no visible area")
    return info


def capture_native(page: Page, cfg: Config) -> np.ndarray:
    info = inspect_canvas(page, cfg, capture=True)
    return decode_canvas(info, cfg)


def decode_canvas(info: dict, cfg: Config) -> np.ndarray:
    data = info["data"]
    prefix = "data:image/png;base64,"
    if not data.startswith(prefix):
        raise RuntimeError("Browser returned an invalid canvas image")
    with Image.open(io.BytesIO(base64.b64decode(data[len(prefix):], validate=True))) as image:
        if image.size != (info["bitmapWidth"], info["bitmapHeight"]):
            raise RuntimeError("Canvas image dimensions changed during capture")
        rgb = np.asarray(image.crop((0, 0, cfg.remote_width, cfg.remote_height)).convert("RGB"), dtype=np.uint8)
    return np.ascontiguousarray(rgb[:, :, ::-1])


def native_point(page: Page, cfg: Config, x: int, y: int) -> tuple[float, float]:
    if not (0 <= x < cfg.remote_width and 0 <= y < cfg.remote_height):
        raise ValueError(f"Point ({x}, {y}) is outside the remote desktop")
    info = inspect_canvas(page, cfg)
    root = display(page, cfg)
    canvas_box = root.locator("canvas").bounding_box()
    display_box = root.bounding_box()
    if canvas_box is None or display_box is None:
        raise RuntimeError("Remote display is not visible")
    px = canvas_box["x"] + x * canvas_box["width"] / info["bitmapWidth"]
    py = canvas_box["y"] + y * canvas_box["height"] / info["bitmapHeight"]
    if not all(math.isfinite(v) for v in (px, py)):
        raise RuntimeError("Invalid remote display coordinates")
    if not (display_box["x"] <= px < display_box["x"] + display_box["width"] and
            display_box["y"] <= py < display_box["y"] + display_box["height"]):
        raise RuntimeError("Remote point is clipped by the display")
    viewport = page.evaluate("() => ({width: innerWidth, height: innerHeight})")
    if not (0 <= px < viewport["width"] and 0 <= py < viewport["height"]):
        raise RuntimeError("Remote point is outside the browser viewport")
    reachable = root.locator("canvas").evaluate("""(canvas, point) => {
      const rect = canvas.getBoundingClientRect();
      const hit = document.elementFromPoint(rect.x + point.x * rect.width / canvas.width,
                                            rect.y + point.y * rect.height / canvas.height);
      return !!hit && (hit === canvas || (hit.contains(canvas) && canvas.parentElement.contains(hit)));
    }""", {"x": x, "y": y})
    if not reachable:
        raise RuntimeError("Remote point is obscured or clipped in the remote frame")
    if cfg.display_frame:
        frame_visible = page.locator(cfg.display_frame).first.evaluate(
            "(frame, point) => document.elementFromPoint(point.x, point.y) === frame", {"x": px, "y": py})
        if not frame_visible:
            raise RuntimeError("Remote frame is obscured at the requested point")
    return px, py
