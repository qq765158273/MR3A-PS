"""Check the MCP operation boundary without opening a browser."""

from contextlib import ExitStack
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np

from psauto.config import Config
from psauto.objects.models import AERequest, FieldRequest, RecordRequest
from psauto.objects.service import ObjectService


class ObjectServiceTests(unittest.TestCase):
    def test_ae_properties_require_native_bound_verified_and_saved_endpoints(self):
        request=AERequest(name='GM_TEST_A',steps=[{'type':'PeopleCode','code':'x'}],
                          state_record='GM_DEPT_AET',disable_restart=True)
        self.completed_names('PSIDE_CreateAE_Saved','PSIDE_CreateAE_SavedAndClosed')
        incomplete=self.service.execute(request)
        self.assertFalse(incomplete['success'])
        self.assertTrue(incomplete['saved'])
        self.assertFalse(incomplete['properties_saved'])
        self.completed_names('PSIDE_CreateAE_Saved','PSIDE_CreateAE_SavedAndClosed',
                             'AEProp_StateBound','AEProp_RestartVerified','AEProp_Saved')
        complete=self.service.execute(request)
        self.assertTrue(complete['success'])
        self.assertTrue(complete['state_record_bound'])
        self.assertTrue(complete['restart_verified'])
        self.assertTrue(complete['properties_saved'])

    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = TemporaryDirectory()
        self.stack.callback(self.cleanup_directory, directory)
        cfg = Config(jumpserver_url='http://127.0.0.1:9')
        cfg.base_dir = Path(directory.name)
        self.service = ObjectService(cfg)
        self.request = FieldRequest(name='GM_TEST_F', long_name='GM Field', short_name='GM')
        module = 'psauto.objects.service.'
        self.session = MagicMock(poisoned=False)
        controller = self.controller = MagicMock()
        controller.post_screencap.return_value.wait.return_value.succeeded = True
        controller.post_screencap.return_value.wait.return_value.get.return_value = np.zeros((2,3,3),dtype=np.uint8)
        self.connect = self.stack.enter_context(patch(module + 'connect_controller',
                                                      return_value=(self.session, controller)))
        self.stack.enter_context(patch(module + 'Toolkit.init_option'))
        self.stack.enter_context(patch(module + 'Tasker.set_stdout_level'))
        self.stack.enter_context(patch(module + 'Tasker.set_debug_mode'))
        self.agent_factory=self.stack.enter_context(patch(module + 'MR3AAgent'))
        self.tasker = MagicMock()
        self.job = self.tasker.post_task.return_value
        self.job.wait.return_value = self.job
        self.job.job_id = 1
        self.job.succeeded = True
        self.stack.enter_context(patch(module + 'create_tasker', return_value=self.tasker))
        self.trace = SimpleNamespace(events=[],close=Mock())
        self.stack.enter_context(patch(module + 'EvidenceSink', return_value=self.trace))
        self.export = self.stack.enter_context(patch(module + 'export_task_evidence'))

    @staticmethod
    def cleanup_directory(directory):
        # Windows can briefly report WinError 145 after deleting fresh test files.
        # Retry only this fixture cleanup; other errors, including open files, fail.
        for attempt in range(3):
            try:
                directory.cleanup()
                return
            except OSError as exc:
                if getattr(exc,'winerror',None)!=145 or attempt==2:
                    raise
                time.sleep(0.05)

    def completed(self, *suffixes):
        self.completed_names(*('PSIDE_CreateField'+suffix for suffix in suffixes))

    def completed_names(self, *names):
        self.trace.events=[{'event':'Node.PipelineNode.Succeeded','details':{'task_id':1,
                           'node_details':{'name':name,'completed':True}}} for name in names]
        self.export.return_value = {'nodes':[{'name':name,'completed':True} for name in names]}

    def test_saved_and_closed_returns_success_and_allows_the_next_operation(self):
        self.completed('_Saved', '_SavedAndClosed')
        first = self.service.execute(self.request)
        second = self.service.execute(self.request)
        self.assertTrue(first['success'])
        self.assertEqual(first['status'], 'saved_and_closed')
        self.assertTrue(first['saved'])
        self.assertTrue(first['workspace_ready'])
        self.assertTrue(second['success'])
        self.assertEqual(self.connect.call_count, 2)
        self.assertEqual(self.tasker.post_task.call_count, 2)
        self.assertEqual(self.session.stop.call_count, 2)

    def test_save_without_close_is_partial_and_blocks_the_next_operation(self):
        self.completed('_Saved')
        result = self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'partial')
        self.assertTrue(result['saved'])
        self.assertTrue(result['may_exist'])
        self.assertFalse(result['workspace_ready'])
        next_result = self.service.execute(self.request)
        self.assertEqual(next_result['status'], 'workspace_not_ready')
        self.assertEqual(self.tasker.post_task.call_count, 1)

    def test_native_job_success_without_save_close_endpoint_is_not_reported_as_success(self):
        self.completed('')
        result = self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertFalse(result['saved'])
        self.assertFalse(result['workspace_ready'])

    def test_failure_reports_the_native_pipeline_location_not_an_earlier_candidate_miss(self):
        self.completed('')
        self.job.succeeded=False
        self.trace.events=[
            {'event':'Node.Recognition.Failed','details':{'name':'query_found','task_id':1}},
            {'event':'Node.PipelineNode.Failed','details':{'name':'F_CloseSaved','task_id':1}},
        ]
        result=self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertEqual(result['failed_node'],'F_CloseSaved')

    def test_candidate_miss_alone_is_not_reported_as_the_failure_location(self):
        self.completed('')
        self.job.succeeded=False
        self.trace.events=[{'event':'Node.Recognition.Failed','details':{'name':'query_found','task_id':1}}]
        self.assertIsNone(self.service.execute(self.request)['failed_node'])

    def test_existing_object_must_be_closed_before_workspace_is_released(self):
        self.completed('_already_exists')
        result = self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertNotEqual(result['status'], 'already_exists')
        self.assertFalse(result['workspace_ready'])
        self.assertTrue(result['may_exist'])

    def test_closed_conflict_allows_the_next_operation(self):
        self.completed('_already_exists', '_conflict_closed')
        result = self.service.execute(self.request)
        self.assertEqual(result['status'], 'already_exists')
        self.assertFalse(result['saved'])
        self.assertTrue(result['workspace_ready'])
        self.completed('_Saved', '_SavedAndClosed')
        self.assertTrue(self.service.execute(self.request)['success'])

    def test_requested_build_requires_build_feedback_before_success(self):
        request=RecordRequest(name='GM_TEST_R',type='SQL Table',fields=['EMPLID'],build=True)
        self.completed_names('PSIDE_CreateRecord_Saved','PSIDE_CreateRecord_SavedAndClosed')
        result=self.service.execute(request)
        self.assertFalse(result['success'])
        self.assertFalse(result['built'])
        self.assertEqual(result['status'],'partial')

    def test_requested_build_returns_success_after_feedback_and_close(self):
        request=RecordRequest(name='GM_TEST_R',type='SQL Table',fields=['EMPLID'],build=True)
        self.completed_names('PSIDE_CreateRecord_Saved','R_BuildFinished','PSIDE_CreateRecord_SavedAndClosed')
        result=self.service.execute(request)
        self.assertTrue(result['success'])
        self.assertTrue(result['built'])
        self.assertTrue(result['workspace_ready'])

    def test_nested_or_uncompleted_markers_cannot_report_a_saved_workspace(self):
        self.completed('')
        for name in ('PSIDE_CreateField_Saved','PSIDE_CreateField_SavedAndClosed'):
            self.trace.events.extend([
                {'event':'Node.PipelineNode.Succeeded','details':{'task_id':2,
                    'node_details':{'name':name,'completed':True}}},
                {'event':'Node.PipelineNode.Succeeded','details':{'task_id':1,
                    'node_details':{'name':name,'completed':False}}},
            ])
        result=self.service.execute(self.request)
        self.assertFalse(result['saved'])
        self.assertFalse(result['workspace_ready'])
        self.assertFalse(result['success'])

    def test_export_failure_keeps_saved_closed_built_facts_and_does_not_replay(self):
        request=RecordRequest(name='GM_TEST_R',type='SQL Table',fields=['EMPLID'],build=True)
        self.completed_names('PSIDE_CreateRecord_Saved','R_BuildFinished','PSIDE_CreateRecord_SavedAndClosed')
        self.export.side_effect=OSError('disk full during export')
        result=self.service.execute(request)
        self.assertTrue(result['success'])
        self.assertEqual(result['status'],'saved_and_closed')
        self.assertTrue(result['saved'])
        self.assertTrue(result['built'])
        self.assertTrue(result['workspace_ready'])
        self.assertEqual(result['evidence_status'],'failed')
        self.assertEqual(result['evidence_errors'][0]['stage'],'task_evidence')
        self.assertFalse(result['next_operation_allowed'])
        self.assertEqual(self.service.execute(request)['status'],'evidence_unavailable')
        self.tasker.post_task.assert_called_once()
        self.session.stop.assert_called_once()
        self.trace.close.assert_called_once()
        json.dumps(result)

    def test_after_png_failure_is_separate_from_business_success(self):
        self.completed('_Saved','_SavedAndClosed')
        with patch('PIL.Image.Image.save',side_effect=OSError('PNG write failed')):
            result=self.service.execute(self.request)
        self.assertTrue(result['success'])
        self.assertTrue(result['saved'])
        self.assertTrue(result['workspace_ready'])
        self.assertEqual(result['evidence_status'],'partial')
        self.assertEqual(result['evidence_errors'][0]['stage'],'after_screenshot')
        self.assertFalse(result['next_operation_allowed'])
        self.session.stop.assert_called_once()

    def test_partial_export_profile_is_written_without_changing_business_facts(self):
        self.completed('_Saved','_SavedAndClosed')
        def export(job, output, trace, *, profile):
            profile.update({'node_access':'streaming','total_ms':12.5,
                            'phases_ms':{'node_detail_ms':10},'counts':{'nodes':1}})
            raise OSError('disk full after first node')
        self.export.side_effect=export
        result=self.service.execute(self.request)
        timings=json.loads((Path(result['evidence_dir'])/'timings.json').read_text(encoding='utf-8'))
        self.assertEqual(timings['evidence_export']['counts']['nodes'],1)
        self.assertEqual(timings['evidence_export']['node_access'],'streaming')
        self.assertIn('evidence_export_ms',timings)
        self.assertTrue(result['saved'])
        self.assertTrue(result['workspace_ready'])
        self.assertEqual(result['evidence_status'],'failed')
        self.assertFalse(result['next_operation_allowed'])
        self.tasker.post_task.assert_called_once()

    def test_timings_and_error_report_failures_cannot_override_the_return(self):
        self.completed('_Saved','_SavedAndClosed')
        original=Path.write_text
        def fail(path,*args,**kwargs):
            if path.name in ('timings.json','error.txt'):raise OSError('unwritable diagnostic file')
            return original(path,*args,**kwargs)
        with patch.object(Path,'write_text',autospec=True,side_effect=fail):
            result=self.service.execute(self.request)
        self.assertTrue(result['success'])
        self.assertTrue(result['saved'])
        self.assertTrue(result['workspace_ready'])
        self.assertEqual(result['evidence_status'],'partial')
        self.assertEqual([e['stage'] for e in result['evidence_errors']],['timings_write','error_report'])
        self.assertFalse(result['next_operation_allowed'])
        self.session.stop.assert_called_once()
        self.tasker.post_task.assert_called_once()
        json.dumps(result)

    def test_unwritable_preflight_does_not_start_the_browser_or_escape(self):
        with patch.object(Path,'write_text',side_effect=OSError('disk unavailable')):
            result=self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertFalse(result['saved'])
        self.assertFalse(result['may_exist'])
        self.assertEqual(result['evidence_status'],'failed')
        self.assertFalse(result['next_operation_allowed'])
        self.assertIn('disk unavailable',result['operation_error'])
        self.connect.assert_not_called()
        self.tasker.post_task.assert_not_called()

    def test_request_only_write_failure_blocks_without_inventing_an_idle_workspace(self):
        original=Path.write_text
        def fail(path,*args,**kwargs):
            if path.name=='request.json':raise OSError('request write failed')
            return original(path,*args,**kwargs)
        with patch.object(Path,'write_text',autospec=True,side_effect=fail):
            result=self.service.execute(self.request)
        self.assertFalse(result['workspace_ready'])
        self.assertFalse(result['may_exist'])
        self.assertFalse(result['next_operation_allowed'])
        self.assertEqual(result['evidence_errors'][0]['stage'],'request_evidence')
        next_result=self.service.execute(self.request)
        self.assertEqual(next_result['status'],'evidence_unavailable')
        self.assertFalse(next_result['workspace_ready'])
        self.connect.assert_not_called()

    def test_export_failure_after_a_partial_save_preserves_partial_outcome(self):
        self.completed('_Saved')
        self.job.succeeded=False
        self.export.side_effect=OSError('report write failed')
        result=self.service.execute(self.request)
        self.assertEqual(result['status'],'partial')
        self.assertTrue(result['saved'])
        self.assertFalse(result['workspace_ready'])
        self.assertFalse(result['success'])
        self.assertEqual(self.service.execute(self.request)['status'],'workspace_not_ready')
        self.tasker.post_task.assert_called_once()

    def test_wait_exception_preserves_the_partial_save_recorded_by_native_events(self):
        self.completed('_Saved')
        self.job.succeeded=False
        self.job.wait.side_effect=RuntimeError('wait interrupted after save')
        result=self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertEqual(result['status'],'partial')
        self.assertTrue(result['saved'])
        self.assertFalse(result['workspace_ready'])
        self.assertIn('wait interrupted',result['operation_error'])
        self.tasker.post_task.assert_called_once()
        self.session.stop.assert_called_once()

    def test_failed_sink_cleanup_does_not_hide_success_or_skip_client_cleanup(self):
        self.completed('_Saved','_SavedAndClosed')
        self.trace.close.side_effect=OSError('sink cleanup failed')
        result=self.service.execute(self.request)
        self.assertTrue(result['success'])
        self.assertTrue(result['workspace_ready'])
        self.assertFalse(result['next_operation_allowed'])
        self.assertEqual(result['evidence_status'],'partial')
        self.assertEqual(result['evidence_errors'][0]['stage'],'event_sink_cleanup')
        self.session.stop.assert_called_once()

    def test_wait_exception_after_close_keeps_facts_but_blocks_the_next_operation(self):
        self.completed('_Saved','_SavedAndClosed')
        self.job.wait.side_effect=RuntimeError('wait failed after close')
        result=self.service.execute(self.request)
        self.assertTrue(result['saved'])
        self.assertTrue(result['workspace_ready'])
        self.assertFalse(result['next_operation_allowed'])
        next_result=self.service.execute(self.request)
        self.assertEqual(next_result['status'],'operation_stopped')
        self.assertTrue(next_result['workspace_ready'])
        self.tasker.post_task.assert_called_once()

    def test_agent_exit_error_keeps_complete_evidence_but_blocks_the_next_operation(self):
        self.completed('_Saved','_SavedAndClosed')
        self.agent_factory.return_value.__exit__.side_effect=RuntimeError('agent exit failed')
        result=self.service.execute(self.request)
        self.assertTrue(result['success'])
        self.assertTrue(result['saved'])
        self.assertTrue(result['workspace_ready'])
        self.assertEqual(result['evidence_status'],'complete')
        self.assertFalse(result['next_operation_allowed'])
        self.assertIn('agent exit failed',result['operation_error'])
        self.assertEqual(self.service.execute(self.request)['status'],'operation_stopped')
        self.tasker.post_task.assert_called_once()
        self.session.stop.assert_called_once()
