"""A client timeout must stop the client and never replay an uncertain action."""
from pathlib import Path
import queue
import unittest
from unittest.mock import Mock, patch

from psauto.cli_controller import PlaywrightCliSession
from psauto.config import Config


class CliTransportTests(unittest.TestCase):
    def test_decode_timing_is_separate_and_failure_keeps_transport_profile(self):
        base=Path(__file__).resolve().parents[2]
        cfg=Config(jumpserver_url='http://offline.invalid',capture_mode='native_canvas',display_selector='#remote',
                   cli_script=str(base/'.psauto-runtime/node_modules/@playwright/cli/playwright-cli.js'),
                   cli_workdir=str(base/'.psauto-runtime'))
        session=PlaywrightCliSession(cfg)
        value={'pixels':'not logged'}
        with patch.object(session,'run_code',return_value={'value':value,'timing':{'body_ms':3,'browser_roundtrip_ms':2}}),\
             patch('psauto.cli_controller.time.perf_counter',side_effect=[0,.010,.011,.025,.030]):
            with self.assertRaisesRegex(ValueError,'bad pixels'):
                session.request('screencap',decoder=Mock(side_effect=ValueError('bad pixels')))
        row=session.timings[0]
        self.assertEqual(row,{'operation':'screencap','elapsed_ms':10,'body_ms':3,
                             'browser_roundtrip_ms':2,'decode_ms':14})
        self.assertNotIn('pixels',str(row))

    def test_timeout_stops_only_the_client_and_rejects_followup_input(self):
        base=Path(__file__).resolve().parents[2]
        cfg=Config(jumpserver_url='http://offline.invalid',capture_mode='native_canvas',display_selector='#remote',
                   cli_script=str(base/'.psauto-runtime/node_modules/@playwright/cli/playwright-cli.js'),
                   cli_workdir=str(base/'.psauto-runtime'))
        session=PlaywrightCliSession(cfg)
        worker=Mock()
        session._worker=worker
        with patch.object(session._responses,'get',side_effect=queue.Empty):
            with self.assertRaises(TimeoutError):
                session.invoke_cli(['run-code','async page => true'])
        self.assertTrue(session.poisoned)
        self.assertIsNone(session._worker)
        self.assertEqual(worker.stdin.write.call_count,1)
        worker.stdin.close.assert_called_once()
        with self.assertRaises(RuntimeError):
            session.invoke_cli(['run-code','async page => true'])
        self.assertEqual(worker.stdin.write.call_count,1)
