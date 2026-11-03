"""Run Maa's browser recovery nodes against the existing Playwright CLI session.

Acknowledging a dialog alone does not mean that the remote desktop has recovered.
This diagnostic entry prints that narrower result and retains its screenshot.
"""

import argparse
import os
import time
from datetime import datetime

from maa.toolkit import Toolkit
from PIL import Image
from maa.tasker import Tasker

from psauto.config import load_config
from psauto.pipeline import create_tasker
from psauto.recovery import connect_recovery_controller
from psauto.cli_controller import PlaywrightCliSession
from psauto.controller import connect_controller
from psauto.evidence import EvidenceSink, export_task_evidence


def recover_idle_session(cfg, simulate_disconnect=False):
    """Run one recognized recovery path, then independently verify RDP and HRDEV.

    Callers must not replay a business operation after this function returns.
    The current implementation only reconnects a browser-saved asset account.
    """
    Tasker.set_debug_mode(True)
    output = cfg.resolve_path('out/recovery/' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    if simulate_disconnect:
        before_session, before_controller = connect_controller(cfg)
        try:
            before_tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), before_controller)
            before_trace = EvidenceSink(before_tasker)
            before = before_tasker.post_task('PSIDE_WindowReady').wait()
            export_task_evidence(before, output / 'before_disconnect', before_trace)
            if not before.succeeded:
                raise RuntimeError('Round-trip precondition failed: HRDEV was not recognized')
        finally:
            before_session.stop()
    session, controller = connect_recovery_controller(cfg)
    try:
        tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), controller)
        entry = 'JumpServer_ReloadSession' if simulate_disconnect else 'JumpServer_Recover'
        trace = EvidenceSink(tasker)
        job = tasker.post_task(entry).wait()
        export_task_evidence(job, output, trace)
        if not job.succeeded:
            raise RuntimeError('No supported recovery state completed; inspect the local recovery report')
    finally:
        session.stop()

    probe = PlaywrightCliSession(cfg)
    deadline = time.monotonic() + 45
    while True:
        try:
            probe.request('inspect')
            break
        except Exception:
            if probe.poisoned or time.monotonic() >= deadline:
                raise RuntimeError('Recovery did not restore the expected RDP canvas; business task remains stopped') from None
            time.sleep(1)
    native_session, native_controller = connect_controller(cfg)
    try:
        native_tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), native_controller)
        native_trace = EvidenceSink(native_tasker)
        verified = native_tasker.post_task('PSIDE_WindowReady').wait()
        export_task_evidence(verified, output / 'remote_check', native_trace)
        if not verified.succeeded:
            raise RuntimeError('RDP returned but HRDEV was not recognized; business task remains stopped')
        print('Recovery verified: native RDP canvas and HRDEV title; business task was not replayed')
        print(f'Evidence: {output}')
    finally:
        native_session.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--acknowledge', action='store_true', help='Acknowledge only the recognized 120-minute timeout')
    parser.add_argument('--recover', action='store_true', help='Run one recognized reconnect path and verify RDP/HRDEV')
    parser.add_argument('--simulate-reconnect', action='store_true', help='Reload a healthy HRDEV connection and test the reconnect round trip')
    args = parser.parse_args()
    cfg = load_config(args.config)
    os.chdir(cfg.base_dir)
    Toolkit.init_option(str(cfg.base_dir))
    if args.recover or args.simulate_reconnect:
        recover_idle_session(cfg, simulate_disconnect=args.simulate_reconnect)
        return 0
    session, controller = connect_recovery_controller(cfg)
    try:
        tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), controller)
        entry = 'JumpServer_AcknowledgeIdleTimeout' if args.acknowledge else 'JumpServer_IdleTimeoutDetected'
        job = tasker.post_task(entry).wait()
        detail = job.get()
        if detail:
            for node in detail.nodes:
                print(f'{node.name}: completed={node.completed}')
        output = cfg.resolve_path('out/recovery_after.png')
        output.parent.mkdir(parents=True, exist_ok=True)
        shot = controller.post_screencap().wait()
        if shot.succeeded:
            Image.fromarray(shot.get()[:, :, ::-1]).save(output)
        print(f'{entry}: {"succeeded" if job.succeeded else "failed"}')
        return 0 if job.succeeded and shot.succeeded else 1
    finally:
        session.stop()


if __name__ == '__main__':
    raise SystemExit(main())
