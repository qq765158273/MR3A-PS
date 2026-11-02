"""Run a MaaFramework pipeline against the configured JumpServer display."""

import argparse
import logging
import os

from maa.toolkit import Toolkit
from PIL import Image

from psauto.config import load_config
from psauto.controller import connect_controller
from psauto.pipeline import create_tasker


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", help="Maa pipeline entry node")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    cfg = load_config(args.config)
    os.chdir(cfg.base_dir)
    Toolkit.init_option(str(cfg.base_dir))
    session, controller = connect_controller(cfg)
    try:
        tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), controller)
        job = tasker.post_task(args.entry).wait()
        detail = job.get()
        if detail is not None:
            for node in detail.nodes:
                hit = node.recognition.hit if node.recognition else None
                print(f"{node.name}: hit={hit} completed={node.completed}")
        print(f"status: {job.status}")
        screenshot = controller.post_screencap().wait()
        if screenshot.succeeded:
            output = cfg.resolve_path("out/after_run.png")
            output.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(screenshot.get()[:, :, ::-1]).save(output)
            print(f"Screenshot: {output}")
        else:
            logging.error("Failed to capture the final screenshot")
        return 0 if job.succeeded and screenshot.succeeded else 1
    finally:
        session.stop()


if __name__ == "__main__":
    raise SystemExit(main())
