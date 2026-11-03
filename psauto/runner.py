"""Interactive login and remote-display diagnostics."""

import argparse
import io
import json
import os
import time

from PIL import Image

from psauto.config import load_config
from psauto.session import BrowserSession, display, open_remote


DUMP_JS = r"""
() => [...document.querySelectorAll('canvas')].map(c => {
  const rect = c.getBoundingClientRect();
  const parents = [];
  for (let e = c.parentElement; e && parents.length < 5; e = e.parentElement) {
    parents.push(e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') +
      (typeof e.className === 'string' && e.className.trim()
        ? '.' + e.className.trim().split(/\s+/).join('.') : ''));
  }
  return {width: c.width, height: c.height, css_width: rect.width, css_height: rect.height,
          x: rect.x, y: rect.y, parents};
})
"""


def cmd_login(cfg, args) -> None:
    cfg.headless = False
    session = BrowserSession(cfg)
    session.start()
    try:
        session.call(lambda page: page.goto(cfg.jumpserver_url))
        input("Complete JumpServer login in the browser, then press Enter here to save the session: ")
        session.save_storage_state()
        print(f"Saved login state: {cfg.resolve_path(cfg.storage_state)}")
    finally:
        session.stop()


def cmd_discover(cfg, args) -> None:
    cfg.headless = False
    session = BrowserSession(cfg)
    session.start()
    try:
        session.call(lambda page: page.goto(cfg.jumpserver_url))
        input("Open the dev/test remote desktop in the browser, then press Enter here: ")

        def collect(page):
            result = []
            for browser_page in page.context.pages:
                for frame in browser_page.frames:
                    try:
                        canvases = frame.evaluate(DUMP_JS)
                        result.append({"page_url": browser_page.url, "frame_url": frame.url,
                                       "frame_name": frame.name, "canvases": canvases})
                    except Exception as exc:
                        result.append({"page_url": browser_page.url, "frame_url": frame.url,
                                       "frame_name": frame.name, "error": str(exc)})
            return result

        print(json.dumps(session.call(collect), ensure_ascii=False, indent=2))
    finally:
        session.stop()


def cmd_probe(cfg, args) -> None:
    output_dir = cfg.resolve_path("out")
    output_dir.mkdir(exist_ok=True)
    if cfg.connection_mode == "cli":
        from psauto.controller import connect_controller

        session, controller = connect_controller(cfg)
        try:
            start = time.monotonic()
            for index, delay in enumerate((0, 3, 10)):
                time.sleep(max(0, start + delay - time.monotonic()))
                job = controller.post_screencap().wait()
                if not job.succeeded:
                    raise RuntimeError("Maa screenshot failed")
                image = job.get()
                path = output_dir / f"probe_{index}.png"
                Image.fromarray(image[:, :, ::-1]).save(path)
                print(f"{path}: image={(image.shape[1], image.shape[0])}")
        finally:
            session.stop()
        return
    session = BrowserSession(cfg)
    session.start()
    try:
        open_remote(session, cfg)
        start = time.monotonic()
        for index, delay in enumerate((0, 3, 10)):
            time.sleep(max(0, start + delay - time.monotonic()))
            if cfg.capture_mode == "native_canvas":
                from psauto.native_canvas import capture_native
                image, box = session.call(lambda page: (
                    capture_native(page, cfg), display(page, cfg).bounding_box()))
                stream = io.BytesIO()
                Image.fromarray(image[:, :, ::-1]).save(stream, format="PNG")
                png = stream.getvalue()
            elif cfg.capture_mode == "viewport":
                png, box = session.call(
                    lambda page: (display(page, cfg).screenshot(), display(page, cfg).bounding_box()))
            else:
                raise ValueError(f"Unsupported capture mode: {cfg.capture_mode}")
            path = output_dir / f"probe_{index}.png"
            path.write_bytes(png)
            with Image.open(path) as image:
                print(f"{path}: image={image.size} box={box}")
    finally:
        session.stop()


def cmd_capture(cfg, args) -> None:
    from psauto.controller import connect_controller

    session, controller = connect_controller(cfg)
    try:
        time.sleep(2)
        if args.click:
            x, y = (int(value.strip()) for value in args.click.split(","))
            clicked = controller.post_click(x, y).wait().succeeded
            print(f"click: {clicked}")
            if not clicked:
                raise RuntimeError("Maa click failed")
            time.sleep(1)
        if args.combo:
            pressed = controller.press_combo(args.combo.split('+'))
            print(f"combo: {pressed}")
            if not pressed:
                raise RuntimeError("Key combination failed")
            time.sleep(1)
        screenshot = controller.post_screencap().wait()
        if not screenshot.succeeded:
            raise RuntimeError("Maa screenshot failed")
        image = screenshot.get()
        path = cfg.resolve_path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(image[:, :, ::-1]).save(path)
        print(f"{path}: shape={image.shape}")
    finally:
        session.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["login", "discover", "probe", "capture"])
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--out", default="out/capture.png")
    parser.add_argument("--click", help="remote display coordinates: X,Y")
    parser.add_argument("--combo", help="Playwright key combination, e.g. Control+o")
    args = parser.parse_args()
    commands = {"login": cmd_login, "discover": cmd_discover,
                "probe": cmd_probe, "capture": cmd_capture}
    cfg = load_config(args.config)
    os.chdir(cfg.base_dir)
    commands[args.command](cfg, args)


if __name__ == "__main__":
    main()
