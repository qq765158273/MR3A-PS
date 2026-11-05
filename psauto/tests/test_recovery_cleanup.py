"""Recovery clients are released on every exit, without opening a browser."""
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from psauto.config import Config
from psauto.recovery import connect_recovery_controller
import recover_session


class RecoveryCleanupTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.cfg=Config(jumpserver_url='http://offline.invalid')
        self.cfg.base_dir=Path(self.stack.enter_context(TemporaryDirectory()))
        self.probe=MagicMock(poisoned=False)
        self.probe.request.side_effect=[{'known':True,'tunnel_state':2},True]
        self.browser=MagicMock();self.native=MagicMock()
        self.recovery_tasker=MagicMock();self.native_tasker=MagicMock()
        self.recovery_tasker.post_task.return_value.wait.return_value.succeeded=True
        self.native_tasker.post_task.return_value.wait.return_value.succeeded=True
        self.stack.enter_context(patch('recover_session.Tasker.set_debug_mode'))
        self.stack.enter_context(patch('recover_session.PlaywrightCliSession',return_value=self.probe))
        self.connect_browser=self.stack.enter_context(patch('recover_session.connect_recovery_controller',
                                                          return_value=(self.browser,MagicMock())))
        self.connect_native=self.stack.enter_context(patch('recover_session.connect_controller',
                                                         return_value=(self.native,MagicMock())))
        self.stack.enter_context(patch('recover_session.create_tasker',side_effect=[self.recovery_tasker,self.native_tasker]))
        self.sink_factory=self.stack.enter_context(patch('recover_session.EvidenceSink'))
        self.export=self.stack.enter_context(patch('recover_session.export_task_evidence',
            side_effect=lambda job,directory,trace: Path(directory).mkdir(parents=True,exist_ok=True)))

    def test_success_releases_probe_recovery_and_native_clients(self):
        recover_session.recover_idle_session(self.cfg,verbose=False)
        for client in (self.probe,self.browser,self.native):client.stop.assert_called_once()
        self.recovery_tasker.post_task.assert_called_once_with('JumpServer_ReloadSession')
        self.native_tasker.post_task.assert_called_once_with('PSIDE_WindowReady')

    def test_probe_start_failure_still_releases_the_probe(self):
        self.probe.request.side_effect=RuntimeError('probe failed')
        with self.assertRaisesRegex(RuntimeError,'probe failed'):
            recover_session.recover_idle_session(self.cfg,verbose=False)
        self.probe.stop.assert_called_once()
        self.connect_browser.assert_not_called()

    def test_recovery_init_failure_releases_the_probe(self):
        self.connect_browser.side_effect=RuntimeError('recovery init failed')
        with self.assertRaisesRegex(RuntimeError,'recovery init failed'):
            recover_session.recover_idle_session(self.cfg,verbose=False)
        self.probe.stop.assert_called_once()
        self.connect_native.assert_not_called()

    def test_failed_recovery_releases_both_created_clients(self):
        self.recovery_tasker.post_task.return_value.wait.return_value.succeeded=False
        with self.assertRaisesRegex(RuntimeError,'No supported recovery state'):
            recover_session.recover_idle_session(self.cfg,verbose=False)
        self.probe.stop.assert_called_once();self.browser.stop.assert_called_once()
        self.connect_native.assert_not_called()

    def test_export_failure_releases_the_event_sink_and_every_created_client(self):
        self.export.side_effect=OSError('recovery export failed')
        with self.assertRaisesRegex(OSError,'recovery export failed'):
            recover_session.recover_idle_session(self.cfg,verbose=False)
        self.sink_factory.return_value.close.assert_called_once()
        self.probe.stop.assert_called_once();self.browser.stop.assert_called_once()
        self.connect_native.assert_not_called()

    def test_failed_transport_postcheck_releases_probe_and_recovery(self):
        self.probe.poisoned=True
        self.probe.request.side_effect=[{'known':True,'tunnel_state':2},RuntimeError('not restored')]
        with self.assertRaisesRegex(RuntimeError,'Recovery did not restore'):
            recover_session.recover_idle_session(self.cfg,verbose=False)
        self.probe.stop.assert_called_once();self.browser.stop.assert_called_once()
        self.connect_native.assert_not_called()

    def test_failed_hrdev_postcheck_releases_all_clients(self):
        self.native_tasker.post_task.return_value.wait.return_value.succeeded=False
        with self.assertRaisesRegex(RuntimeError,'HRDEV was not recognized'):
            recover_session.recover_idle_session(self.cfg,verbose=False)
        for client in (self.probe,self.browser,self.native):client.stop.assert_called_once()

    def test_failed_disconnect_precondition_releases_probe_and_native_client(self):
        self.recovery_tasker.post_task.return_value.wait.return_value.succeeded=False
        with self.assertRaisesRegex(RuntimeError,'Round-trip precondition failed'):
            recover_session.recover_idle_session(self.cfg,simulate_disconnect=True,verbose=False)
        self.probe.stop.assert_called_once();self.native.stop.assert_called_once()
        self.connect_browser.assert_not_called()

    def test_recovery_controller_initializer_releases_session_on_failure_only(self):
        for failure in ('constructor','size','connection',None):
            with self.subTest(failure=failure):
                session=MagicMock();controller=MagicMock()
                controller.set_screenshot_use_raw_size.return_value=failure!='size'
                controller.post_connection.return_value.wait.return_value.succeeded=failure!='connection'
                with patch('psauto.recovery.BrowserRecoverySession',return_value=session), \
                     patch('psauto.recovery.BrowserRecoveryController',return_value=controller,
                           side_effect=RuntimeError('constructor failed') if failure=='constructor' else None):
                    if failure is None:
                        self.assertEqual(connect_recovery_controller(self.cfg),(session,controller))
                        session.stop.assert_not_called()
                    else:
                        with self.assertRaises(RuntimeError):connect_recovery_controller(self.cfg)
                        session.stop.assert_called_once()
