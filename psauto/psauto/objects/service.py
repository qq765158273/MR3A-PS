"""Serialize native Maa tasks; success means saved/closed, DB verifies content."""

import copy
from datetime import datetime
import json
from pathlib import Path
import threading
import time

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


def _business_result(entry, request, job, trace):
    """Read terminal facts from the native task's events, without exporting images."""
    events = [event for event in trace.events if event['details'].get('task_id') == job.job_id]
    completed = {
        event['details']['node_details']['name'] for event in events
        if event['event'] == 'Node.PipelineNode.Succeeded'
        and event['details'].get('node_details', {}).get('completed') is True
    }
    may_exist = any(event['event'] == 'Node.Action.Starting'
                    and event['details'].get('name', '').endswith('_ok') for event in events)
    saved = entry + '_Saved' in completed
    closed = entry + '_SavedAndClosed' in completed
    built = 'R_BuildFinished' in completed
    build_required = isinstance(request, RecordRequest) and request.build
    ae_request = isinstance(request, AERequest)
    state_required = ae_request and request.state_record is not None
    restart_required = ae_request and request.disable_restart is not None
    properties_required = state_required or restart_required
    state_bound = 'AEProp_StateBound' in completed
    restart_verified = 'AEProp_RestartVerified' in completed
    properties_saved = 'AEProp_Saved' in completed
    conflict = entry + '_already_exists' in completed
    conflict_closed = entry + '_conflict_closed' in completed
    success = bool(job.succeeded and saved and closed and (not build_required or built)
                   and (not state_required or state_bound)
                   and (not restart_required or restart_verified)
                   and (not properties_required or properties_saved))
    status = ('saved_and_closed' if success else
              'already_exists' if conflict and conflict_closed and job.succeeded else
              'partial' if saved or may_exist else 'failed')
    failures = [event['details'].get('name') for event in events
                if event['event'] == 'Node.PipelineNode.Failed']
    return {'success': success, 'status': status, 'name': request.name,
            'saved': saved, 'workspace_ready': closed or conflict_closed,
            **({'built': built} if build_required else {}),
            **({'state_record_bound': state_bound} if state_required else {}),
            **({'restart_verified': restart_verified} if restart_required else {}),
            **({'properties_saved': properties_saved} if properties_required else {}),
            'may_exist': may_exist or saved or conflict,
            'failed_node': failures[-1] if failures and not success and not conflict_closed else None}


class ObjectService:
    def __init__(self, cfg):
        self.cfg = cfg
        self._lock = threading.Lock()
        self._uncertain_timeout = False
        self._workspace_blocked = False
        self._evidence_blocked = False
        self._operation_blocked = False
        self._last_workspace_ready = False

    def execute(self, request):
        entry, override = BUILDERS[type(request)](request)
        with self._lock:
            if self._uncertain_timeout:
                return {'success': False, 'status': 'session_stopped', 'name': request.name,
                        'workspace_ready': False, 'next_operation_allowed': False,
                        'message': 'A previous CLI timeout has an uncertain outcome; inspect the session before restarting the MCP server'}
            if self._workspace_blocked:
                return {'success': False, 'status': 'workspace_not_ready', 'name': request.name,
                        'workspace_ready': False, 'next_operation_allowed': False,
                        'message': 'The previous operation did not return to the idle workspace; inspect it before restarting the MCP server'}
            if self._evidence_blocked:
                return {'success': False, 'status': 'evidence_unavailable', 'name': request.name,
                        'workspace_ready': self._last_workspace_ready, 'next_operation_allowed': False,
                        'message': 'A previous call has incomplete evidence; resolve the evidence failure before restarting the MCP server'}
            if self._operation_blocked:
                return {'success': False, 'status': 'operation_stopped', 'name': request.name,
                        'workspace_ready': self._last_workspace_ready, 'next_operation_allowed': False,
                        'message': 'A previous operation raised an error; inspect its known outcome before restarting the MCP server'}
            cfg = copy.copy(self.cfg)
            cfg.text_input_mode = 'clipboard'
            output = cfg.resolve_path('out/objects/' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            session = None
            trace = None
            job = None
            task_started = False
            evidence_complete = False
            outcome_recorded = False
            evidence_errors = []
            operation_error = None
            timings = {}
            result = {'success': False, 'status': 'failed', 'name': request.name,
                      'saved': False, 'workspace_ready': False, 'may_exist': False,
                      'failed_node': None, 'evidence_dir': str(output)}

            def evidence_error(stage, exc):
                evidence_errors.append({'stage': stage, 'error': f'{type(exc).__name__}: {exc}'[:1000]})
                self._evidence_blocked = True

            try:
                try:
                    output.mkdir(parents=True, exist_ok=True)
                    (output / 'request.json').write_text(request.model_dump_json(indent=2), encoding='utf-8')
                    (output / 'pipeline_override.json').write_text(json.dumps(override, ensure_ascii=False, indent=2), encoding='utf-8')
                except Exception as exc:
                    evidence_error('request_evidence', exc)
                    raise
                Toolkit.init_option(str(cfg.base_dir))
                Tasker.set_stdout_level(LoggingLevelEnum.Off)
                Tasker.set_debug_mode(True)
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
                    started = time.perf_counter()
                    job = tasker.post_task(entry, override)
                    job.wait()
                    timings['pipeline_ms'] = round((time.perf_counter() - started) * 1000, 2)
                    result.update(_business_result(entry, request, job, trace))
                    outcome_recorded = True
                    self._workspace_blocked = not result['workspace_ready']
                    started = time.perf_counter()
                    export_profile = {}
                    try:
                        export_task_evidence(job, output, trace, profile=export_profile)
                        evidence_complete = True
                    except Exception as exc:
                        evidence_error('task_evidence', exc)
                    finally:
                        timings['evidence_export_ms'] = round((time.perf_counter() - started) * 1000, 2)
                        timings['evidence_export'] = export_profile
                    try:
                        shot = controller.post_screencap().wait()
                        if not shot.succeeded:
                            raise RuntimeError('Final evidence screenshot was not captured')
                        Image.fromarray(shot.get()[:, :, ::-1]).save(output / 'after.png')
                    except Exception as exc:
                        evidence_error('after_screenshot', exc)
            except Exception as exc:
                operation_error = f'{type(exc).__name__}: {exc}'
                self._operation_blocked = task_started
                if job is not None and trace is not None and not outcome_recorded:
                    try:
                        result.update(_business_result(entry, request, job, trace))
                    except Exception as state_exc:
                        evidence_error('business_state_read', state_exc)
                if task_started and not result['workspace_ready']:
                    self._workspace_blocked = True
                result['may_exist'] = result['may_exist'] or task_started
                result['message'] = 'Automation stopped; inspect the local evidence. The task was not replayed.'
            finally:
                if trace is not None:
                    try:
                        trace.close()
                    except Exception as exc:
                        evidence_error('event_sink_cleanup', exc)
                if session is not None:
                    try:
                        self._uncertain_timeout = self._uncertain_timeout or bool(session.poisoned)
                        transport = getattr(session, 'timings', [])
                        if not isinstance(transport, list):
                            transport = []
                        cli_settings = getattr(session, 'cli_settings', {})
                        if isinstance(cli_settings, dict) and cli_settings:
                            timings['cli_settings'] = cli_settings
                        timings['transport'] = transport
                    except Exception as exc:
                        evidence_error('timings_read', exc)
                    finally:
                        try:
                            session.stop()
                        except Exception as exc:
                            self._uncertain_timeout = True
                            evidence_error('client_cleanup', exc)
                try:
                    (output / 'timings.json').write_text(json.dumps(timings, indent=2), encoding='utf-8')
                except Exception as exc:
                    evidence_error('timings_write', exc)
            if operation_error or evidence_errors:
                try:
                    lines = ([operation_error] if operation_error else []) + [
                        f"{error['stage']}: {error['error']}" for error in evidence_errors]
                    (output / 'error.txt').write_text('\n'.join(lines), encoding='utf-8')
                except Exception as exc:
                    evidence_error('error_report', exc)
            result['evidence_status'] = ('partial' if evidence_errors else 'complete') if evidence_complete else 'failed'
            if operation_error:
                result['operation_error'] = operation_error[:1000]
            if evidence_errors:
                result['evidence_errors'] = evidence_errors
            self._last_workspace_ready = result['workspace_ready']
            result['next_operation_allowed'] = not (self._uncertain_timeout or self._workspace_blocked
                                                    or self._evidence_blocked or self._operation_blocked)
            return result
