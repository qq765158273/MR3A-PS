"""Run a MaaFramework pipeline against the configured JumpServer display."""

import argparse
import logging
import os
import json
from datetime import datetime
from pathlib import Path

from maa.toolkit import Toolkit
from maa.tasker import Tasker
from PIL import Image

from psauto.agent_bridge import MR3AAgent
from psauto.config import load_config
from psauto.controller import connect_controller
from psauto.pipeline import create_tasker
from psauto.evidence import EvidenceSink, export_task_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", help="Maa pipeline entry node")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--override", help="JSON file passed directly to Maa pipeline_override")
    parser.add_argument("--no-recovery", action="store_true", help="Stop immediately if the RDP preflight fails")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    cfg = load_config(args.config)
    override = json.loads(Path(args.override).read_text(encoding='utf-8')) if args.override else {}
    os.chdir(cfg.base_dir)
    Toolkit.init_option(str(cfg.base_dir))
    Tasker.set_debug_mode(True)
    try:
        session, controller = connect_controller(cfg)
    except RuntimeError:
        if cfg.connection_mode != 'cli' or args.no_recovery:
            raise
        from recover_session import recover_idle_session
        recover_idle_session(cfg)
        session, controller = connect_controller(cfg)
    try:
        with MR3AAgent(Path(__file__).resolve().parent.parent) as agent_client:
            tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), controller, agent_client)
            trace = EvidenceSink(tasker)
            job = tasker.post_task(args.entry, override).wait()
            evidence_dir = cfg.resolve_path('out/runs/' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            export_task_evidence(job, evidence_dir, trace)
            (evidence_dir / 'override.json').write_text(json.dumps(override, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'Evidence: {evidence_dir}')
            detail = job.get()
            if detail is not None:
                for node in detail.nodes:
                    hit = node.recognition.hit if node.recognition else None
                    print(f"{node.name}: hit={hit} completed={node.completed}")
            print(f"status: {'succeeded' if job.succeeded else 'failed'}")
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
