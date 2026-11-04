"""Serialize native Maa tasks; success means saved/closed, DB verifies content."""

import copy
from datetime import datetime
import json
from pathlib import Path
import threading

from maa.define import LoggingLevelEnum
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from PIL import Image

from ..agent_bridge import MR3AAgent
from ..controller import connect_controller
from ..evidence import EvidenceSink, export_task_evidence
from ..pipeline import create_tasker
from . import ae, field, record
from .models import AERequest, FieldRequest, RecordRequest


BUILDERS = {FieldRequest: field.build, RecordRequest: record.build, AERequest: ae.build}


class ObjectService:
    def __init__(self, cfg):
        self.cfg = cfg
        self._lock = threading.Lock()
        self._uncertain_timeout = False
        self._workspace_blocked = False

    def execute(self, request):
        entry, override = BUILDERS[type(request)](request)
        with self._lock:
            if self._uncertain_timeout:
                return {'success': False, 'status': 'session_stopped', 'name': request.name,
                        'workspace_ready': False,
                        'message': 'A previous CLI timeout has an uncertain outcome; inspect the session before restarting the MCP server'}
            if self._workspace_blocked:
                return {'success': False, 'status': 'workspace_not_ready', 'name': request.name,
                        'workspace_ready': False,
                        'message': 'The previous operation did not return to the idle workspace; inspect it before restarting the MCP server'}
            cfg = copy.copy(self.cfg)
            cfg.text_input_mode = 'clipboard'
            output = cfg.resolve_path('out/objects/' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            output.mkdir(parents=True, exist_ok=True)
            (output / 'request.json').write_text(request.model_dump_json(indent=2), encoding='utf-8')
            (output / 'pipeline_override.json').write_text(json.dumps(override, ensure_ascii=False, indent=2), encoding='utf-8')
            Toolkit.init_option(str(cfg.base_dir))
            Tasker.set_stdout_level(LoggingLevelEnum.Off)
            Tasker.set_debug_mode(True)
            session = None
            trace = None
            task_started = False
            saved = workspace_ready = may_exist = False
            try:
                try:
                    session, controller = connect_controller(cfg)
                except RuntimeError:
                    from recover_session import recover_idle_session
                    recover_idle_session(cfg, verbose=False)
                    session, controller = connect_controller(cfg)
                with MR3AAgent(Path(__file__).resolve().parents[3]) as agent:
                    tasker = create_tasker(str(cfg.resolve_path(cfg.resource_dir)), controller, agent)
                    trace = EvidenceSink(tasker)
                    task_started = True
                    job = tasker.post_task(entry, override).wait()
                    report = export_task_evidence(job, output, trace)
                    completed = {n['name'] for n in report['nodes'] if n['completed']}
                    may_exist = any(e['event'] == 'Node.Action.Starting' and e['details'].get('name', '').endswith('_ok')
                                    for e in trace.events)
                    saved = entry + '_Saved' in completed
                    closed = entry + '_SavedAndClosed' in completed
                    built = 'R_BuildFinished' in completed
                    build_required = isinstance(request, RecordRequest) and request.build
                    conflict = entry + '_already_exists' in completed
                    conflict_closed = entry + '_conflict_closed' in completed
                    workspace_ready = closed or conflict_closed
                    success = job.succeeded and saved and closed and (not build_required or built)
                    status = ('saved_and_closed' if success else
                              'already_exists' if conflict and conflict_closed and job.succeeded else
                              'partial' if saved or may_exist else 'failed')
                    self._workspace_blocked = not workspace_ready
                    failures = [e['details'].get('name') for e in trace.events
                                if e['event'] in ('Node.Recognition.Failed', 'Node.Action.Failed')]
                    shot = controller.post_screencap().wait()
                    if shot.succeeded:
                        Image.fromarray(shot.get()[:, :, ::-1]).save(output / 'after.png')
                    self._uncertain_timeout = session.poisoned
                    return {'success': success, 'status': status, 'name': request.name,
                            'saved': saved, 'workspace_ready': workspace_ready,
                            **({'built': built} if build_required else {}),
                            'may_exist': may_exist or saved or conflict,
                            'failed_node': failures[-1] if failures and not success and not conflict_closed else None,
                            'evidence_dir': str(output)}
            except Exception as exc:
                if session is not None and session.poisoned:
                    self._uncertain_timeout = True
                if task_started and not workspace_ready:
                    self._workspace_blocked = True
                (output / 'error.txt').write_text(f'{type(exc).__name__}: {exc}', encoding='utf-8')
                return {'success': False, 'status': 'failed', 'name': request.name,
                        'saved': saved, 'workspace_ready': workspace_ready,
                        'may_exist': saved or may_exist or task_started,
                        'message': 'Automation stopped; inspect the local evidence. The task was not replayed.',
                        'evidence_dir': str(output)}
            finally:
                if session is not None:
                    session.stop()
