"""Check the MCP operation boundary without opening a browser."""

from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from psauto.config import Config
from psauto.objects.models import FieldRequest, RecordRequest
from psauto.objects.service import ObjectService


class ObjectServiceTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        directory = self.stack.enter_context(TemporaryDirectory())
        cfg = Config(jumpserver_url='http://127.0.0.1:9')
        cfg.base_dir = Path(directory)
        self.service = ObjectService(cfg)
        self.request = FieldRequest(name='GM_TEST_F', long_name='GM Field', short_name='GM')
        module = 'psauto.objects.service.'
        self.session = MagicMock(poisoned=False)
        controller = MagicMock()
        controller.post_screencap.return_value.wait.return_value.succeeded = False
        self.connect = self.stack.enter_context(patch(module + 'connect_controller',
                                                      return_value=(self.session, controller)))
        self.stack.enter_context(patch(module + 'Toolkit.init_option'))
        self.stack.enter_context(patch(module + 'Tasker.set_stdout_level'))
        self.stack.enter_context(patch(module + 'Tasker.set_debug_mode'))
        self.stack.enter_context(patch(module + 'MR3AAgent'))
        self.tasker = MagicMock()
        self.job = self.tasker.post_task.return_value.wait.return_value
        self.job.succeeded = True
        self.stack.enter_context(patch(module + 'create_tasker', return_value=self.tasker))
        self.trace = SimpleNamespace(events=[])
        self.stack.enter_context(patch(module + 'EvidenceSink', return_value=self.trace))
        self.export = self.stack.enter_context(patch(module + 'export_task_evidence'))

    def completed(self, *suffixes):
        self.export.return_value = {'nodes': [dict(name='PSIDE_CreateField' + suffix, completed=True)
                                              for suffix in suffixes]}

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
            {'event':'Node.Recognition.Failed','details':{'name':'query_found'}},
            {'event':'Node.PipelineNode.Failed','details':{'name':'F_CloseSaved'}},
        ]
        result=self.service.execute(self.request)
        self.assertFalse(result['success'])
        self.assertEqual(result['failed_node'],'F_CloseSaved')

    def test_candidate_miss_alone_is_not_reported_as_the_failure_location(self):
        self.completed('')
        self.job.succeeded=False
        self.trace.events=[{'event':'Node.Recognition.Failed','details':{'name':'query_found'}}]
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
        self.export.return_value={'nodes':[{'name':'PSIDE_CreateRecord'+suffix,'completed':True}
                                          for suffix in ('_Saved','_SavedAndClosed')]}
        result=self.service.execute(request)
        self.assertFalse(result['success'])
        self.assertFalse(result['built'])
        self.assertEqual(result['status'],'partial')

    def test_requested_build_returns_success_after_feedback_and_close(self):
        request=RecordRequest(name='GM_TEST_R',type='SQL Table',fields=['EMPLID'],build=True)
        self.export.return_value={'nodes':[{'name':name,'completed':True} for name in
            ('PSIDE_CreateRecord_Saved','R_BuildFinished','PSIDE_CreateRecord_SavedAndClosed')]}
        result=self.service.execute(request)
        self.assertTrue(result['success'])
        self.assertTrue(result['built'])
        self.assertTrue(result['workspace_ready'])
