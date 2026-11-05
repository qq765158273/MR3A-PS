"""Exercise Maa against a disposable Playwright CLI session and local page."""

import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
import uuid
from unittest.mock import patch

from test_browser_session import Handler


@unittest.skipUnless(os.environ.get("PSAUTO_TEST_CLI"), "CLI integration not enabled")
class CliControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cli = Path(os.environ.get('PSAUTO_TEST_CLI_SCRIPT') or
                       Path(__file__).resolve().parents[2] / ".psauto-runtime/node_modules/@playwright/cli/playwright-cli.js")
        cls.node = shutil.which("node")
        if not cls.node or not cls.cli.is_file():
            raise RuntimeError("Project-local Playwright CLI is not installed")
        cls.temp = tempfile.TemporaryDirectory()
        cls.session_name = "psauto-test-" + uuid.uuid4().hex[:12]
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        url = f"http://127.0.0.1:{cls.server.server_port}/native"
        options = []
        if os.environ.get('PSAUTO_TEST_CLI_SETTLE_MS') is not None:
            config_file = Path(cls.temp.name) / 'cli.json'
            config_file.write_text(json.dumps({'timeouts': {'settle': int(os.environ['PSAUTO_TEST_CLI_SETTLE_MS'])},
                                              'browser': {'launchOptions': {'headless': True}}}), encoding='utf-8')
            options.append(f'--config={config_file}')
        result = subprocess.run([cls.node, str(cls.cli), f"-s={cls.session_name}", "open", url,
                                 "--browser=chrome", *options], cwd=cls.temp.name, capture_output=True,
                                encoding="utf-8", timeout=60)
        if result.returncode:
            cls.server.shutdown()
            cls.server.server_close()
            cls.server_thread.join()
            cls.temp.cleanup()
            raise RuntimeError(f"Unable to start test CLI session: {result.stderr or result.stdout}")

    @classmethod
    def tearDownClass(cls):
        try:
            subprocess.run([cls.node, str(cls.cli), f"-s={cls.session_name}", "close"],
                           cwd=cls.temp.name, capture_output=True, timeout=30)
        finally:
            cls.server.shutdown()
            cls.server.server_close()
            cls.server_thread.join()
            cls.temp.cleanup()

    def test_maa_screenshot_and_scaled_click(self):
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.controller import connect_controller

        Toolkit.init_option(".")
        cfg = Config(jumpserver_url="http://127.0.0.1", display_selector="#remote",
                     connection_mode="cli", cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir=".", capture_mode="native_canvas",canvas_refresh_mode="browser")
        cfg.base_dir = Path(self.temp.name)
        session, controller = connect_controller(cfg)
        try:
            job = controller.post_screencap().wait()
            self.assertTrue(job.succeeded)
            image = job.get()
            self.assertEqual(image.shape, (1080, 1920, 3))
            self.assertEqual(image[120, 120].tolist(), [40, 230, 0])
            self.assertTrue(controller.post_click(120, 140).wait().succeeded)
            result = subprocess.run([self.node, str(self.cli), f"-s={self.session_name}", "--raw",
                                     "eval", "() => document.body.dataset.point"],
                                    cwd=self.temp.name, capture_output=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip().strip('"'), "120,140")
        finally:
            session.stop()

    def test_batched_shortcut_and_client_shutdown_preserve_the_browser(self):
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.controller import connect_controller
        Toolkit.init_option('.')
        cfg = Config(jumpserver_url='http://127.0.0.1', display_selector='#remote',
                     connection_mode='cli', cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir='.', capture_mode='native_canvas',canvas_refresh_mode='browser')
        cfg.base_dir = Path(self.temp.name)
        session, controller = connect_controller(cfg)
        try:
            session.run_code('''async page => {
                await page.locator('#remote').evaluate(el => {
                    const sink=document.createElement('textarea'); el.appendChild(sink); sink.focus();
                    window.chordEvents=[];
                    sink.addEventListener('keydown',e=>window.chordEvents.push({key:e.key,ctrl:e.ctrlKey}));
                }); return true;
            }''')
            worker = session._worker
            self.assertTrue(controller.post_click_key(0x2000D).wait().succeeded)
            self.assertIs(session._worker, worker)
            events=session.run_code('async page => page.evaluate(() => chordEvents)')
            self.assertTrue(any(e['key']=='Enter' and e['ctrl'] for e in events))
            session.stop()
            self.assertIsNotNone(worker.poll())
            # The official browser daemon survives our persistent client stopping.
            check = subprocess.run([self.node,str(self.cli),f'-s={self.session_name}','--raw','eval',
                                    '() => true'],cwd=self.temp.name,capture_output=True,text=True,timeout=30)
            self.assertEqual(check.returncode,0)
        finally:
            subprocess.run([self.node,str(self.cli),f'-s={self.session_name}','--raw','goto',
                            f'http://127.0.0.1:{self.server.server_port}/native'],
                           cwd=self.temp.name,capture_output=True,timeout=30)
            session.stop()

    def test_effective_settle_is_checked_before_any_browser_action(self):
        from psauto.config import Config
        from psauto.cli_controller import PlaywrightCliSession
        cfg=Config(jumpserver_url='http://127.0.0.1',display_selector='#remote',
                   connection_mode='cli',cli_session=self.session_name,
                   cli_script=str(self.cli),cli_workdir='.',capture_mode='native_canvas',
                   canvas_refresh_mode='browser')
        cfg.base_dir=Path(self.temp.name)
        session=PlaywrightCliSession(cfg)
        try:
            effective=json.loads(session.invoke_cli(['config-print']).stdout)['timeouts']['settle']
            session.run_code('''async page=>{
                await page.goto('''+json.dumps(f'http://127.0.0.1:{self.server.server_port}/native')+''');
                await page.locator('#remote').evaluate(el=>{
                    const sink=document.createElement('textarea');el.appendChild(sink);sink.focus();
                    window.inputCount=0;sink.addEventListener('keydown',()=>inputCount++);
                });return true;
            }''')
            session.stop()
            cfg.cli_settle_ms=effective+1
            with self.assertRaisesRegex(RuntimeError,'Playwright CLI settle is'):
                session.request('key',key='Enter')
            session.stop()
            cfg.cli_settle_ms=effective
            self.assertTrue(session.request('inspect',prepare=True))
            self.assertEqual(session.cli_settings,{'expected_settle_ms':effective,'effective_settle_ms':effective})
            self.assertEqual(session.run_code('async page=>page.evaluate(()=>inputCount)'),0)
            self.assertTrue(session.request('key',key='Enter'))
            self.assertEqual(session.run_code('async page=>page.evaluate(()=>inputCount)'),1)
        finally:
            session.stop()
            subprocess.run([self.node,str(self.cli),f'-s={self.session_name}','--raw','goto',
                            f'http://127.0.0.1:{self.server.server_port}/native'],
                           cwd=self.temp.name,capture_output=True,timeout=30)

    def test_original_mr3a_agent_is_available(self):
        from maa.resource import Resource
        from maa.toolkit import Toolkit
        from psauto.agent_bridge import MR3AAgent

        Toolkit.init_option(".")
        with MR3AAgent(Path(__file__).resolve().parents[2]) as agent:
            resource = Resource()
            self.assertTrue(agent.bind(resource))
            self.assertTrue(agent.connect())
            self.assertTrue(agent.connected)
            self.assertIn("DisableNode", agent.custom_action_list)
            self.assertIn("MultiRecognition", agent.custom_recognition_list)

    def test_prepare_retries_only_a_readonly_screenshot_and_bounds_repeated_timeouts(self):
        from psauto.config import Config
        from psauto.cli_controller import PlaywrightCliSession
        cfg=Config(jumpserver_url='http://127.0.0.1',display_selector='#remote',
                   connection_mode='cli',cli_session=self.session_name,
                   cli_script=str(self.cli),cli_workdir='.',capture_mode='native_canvas',canvas_refresh_mode='browser')
        cfg.base_dir=Path(self.temp.name)
        session=PlaywrightCliSession(cfg)
        try:
            session.run_code('async page=>{await page.goto('+json.dumps(f'http://127.0.0.1:{self.server.server_port}/native')+');return true;}')
            session.run_code('''async page=>{
                page.__realScreenshot=page.screenshot.bind(page);
                page.__captureCalls=0; page.__alwaysFailCapture=false;
                page.screenshot=async options=>{
                    page.__captureCalls++;
                    if(page.__captureCalls===1 || page.__alwaysFailCapture)
                        throw new Error('page.screenshot: Timeout 5000ms exceeded.');
                    return page.__realScreenshot(options);
                };
                await page.locator('#remote').evaluate(el=>{
                    const sink=document.createElement('textarea');el.appendChild(sink);
                    window.inputCount=0;sink.addEventListener('keydown',()=>inputCount++);
                });
                return true;
            }''')
            self.assertTrue(session.request('inspect',prepare=True))
            self.assertEqual(session.run_code('async page=>page.__captureCalls'),2)
            self.assertEqual(session.run_code('async page=>page.evaluate(()=>inputCount)'),0)
            session.run_code('async page=>{page.__captureCalls=0;page.__alwaysFailCapture=true;return true;}')
            with self.assertRaisesRegex(RuntimeError,'page.screenshot: Timeout'):
                session.request('inspect',prepare=True)
            self.assertEqual(session.run_code('async page=>page.__captureCalls'),2)
            self.assertEqual(session.run_code('async page=>page.evaluate(()=>inputCount)'),0)
        finally:
            session.run_code('''async page=>{
                page.screenshot=page.__realScreenshot;
                delete page.__realScreenshot;delete page.__captureCalls;delete page.__alwaysFailCapture;
                await page.goto('''+json.dumps(f'http://127.0.0.1:{self.server.server_port}/native')+''');
                return true;
            }''')
            session.stop()

    def test_maa_swipe_and_unicode_input(self):
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.controller import connect_controller

        Toolkit.init_option(".")
        cfg = Config(jumpserver_url="http://127.0.0.1", display_selector="#remote",
                     connection_mode="cli", cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir=".", capture_mode="native_canvas",canvas_refresh_mode="browser")
        cfg.base_dir = Path(self.temp.name)
        session, controller = connect_controller(cfg)
        try:
            self.assertTrue(controller.post_swipe(120, 140, 300, 220, 100).wait().succeeded)
            command = [self.node, str(self.cli), f"-s={self.session_name}", "--raw", "eval"]
            result = subprocess.run(command + ["() => document.body.dataset.drag"], cwd=self.temp.name,
                                    capture_output=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.stdout.strip().strip('"'), "up")
            setup = "() => { const el = document.createElement('textarea'); el.id = 'input-test'; document.querySelector('#remote').appendChild(el); el.focus(); }"
            result = subprocess.run(command + [setup], cwd=self.temp.name, capture_output=True,
                                    encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(controller.post_input_text("测试A").wait().succeeded)
            result = subprocess.run(command + ["() => document.querySelector('#input-test').value"],
                                    cwd=self.temp.name, capture_output=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.stdout.strip().strip('"'), "测试A")
        finally:
            session.stop()

    def test_pipeline_executes_existing_mr3a_action(self):
        from maa.toolkit import Toolkit
        from psauto.agent_bridge import MR3AAgent
        from psauto.config import Config
        from psauto.controller import connect_controller
        from psauto.pipeline import create_tasker

        Toolkit.init_option(".")
        cfg = Config(jumpserver_url="http://127.0.0.1", display_selector="#remote",
                     connection_mode="cli", cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir=".", capture_mode="native_canvas",canvas_refresh_mode="browser")
        cfg.base_dir = Path(self.temp.name)
        bundle = Path(self.temp.name) / "mr3a-test-resource"
        (bundle / "pipeline").mkdir(parents=True, exist_ok=True)
        (bundle / "pipeline/test.json").write_text(json.dumps({
            "UseOriginalDisableNode": {
                "recognition": "DirectHit",
                "action": {"type": "Custom", "param": {"custom_action": "DisableNode",
                            "custom_action_param": {"node_name": "LocalUnused"}}}
            },
            "LocalUnused": {"recognition": "DirectHit"}
        }), encoding="utf-8")
        session, controller = connect_controller(cfg)
        try:
            with MR3AAgent(Path(__file__).resolve().parents[2]) as agent:
                tasker = create_tasker(str(bundle), controller, agent)
                job = tasker.post_task("UseOriginalDisableNode").wait()
                self.assertTrue(job.succeeded)
        finally:
            session.stop()

    @unittest.skipUnless(os.environ.get("PSAUTO_TEST_OCR"), "OCR integration not enabled")
    def test_demo_releases_control_when_key_fails(self):
        from maa.toolkit import Toolkit
        from psauto.agent_bridge import MR3AAgent
        from psauto.config import Config
        from psauto.controller import connect_controller
        from psauto.pipeline import create_tasker

        Toolkit.init_option(".")
        cfg = Config(jumpserver_url="http://127.0.0.1", display_selector="#remote",
                     connection_mode="cli", cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir=".", capture_mode="native_canvas",canvas_refresh_mode="browser")
        cfg.base_dir = Path(self.temp.name)
        bundle = Path(self.temp.name) / "pside-error-test-resource"
        (bundle / "pipeline").mkdir(parents=True, exist_ok=True)
        source = Path(__file__).resolve().parents[2] / "assets/resource/pipeline/PSIDE/ready.json"
        shutil.copy(source, bundle / "pipeline/ready.json")
        model = Path(__file__).resolve().parents[2] / "assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn"
        shutil.copytree(model, bundle / "model/ocr")
        session, controller = connect_controller(cfg)
        operations = []
        request = session.request

        def fail_o(operation, **params):
            operations.append((operation, params.get("key")))
            if operation == "key" and params.get("key") == "o":
                raise RuntimeError("Simulated key failure")
            return request(operation, **params)

        try:
            with MR3AAgent(Path(__file__).resolve().parents[2]) as agent:
                tasker = create_tasker(str(bundle), controller, agent)
                self.assertTrue(controller.post_click(120, 140).wait().succeeded)
                with patch.object(session, "request", side_effect=fail_o):
                    job = tasker.post_task("PSIDE_Demo").wait()
                detail = job.get()
                self.assertTrue(job.failed, f"failed={job.failed} succeeded={job.succeeded} "
                    f"nodes={[(n.name, n.completed) for n in detail.nodes] if detail else None}")
                self.assertIn(("key_down", "Control"), operations)
                self.assertIn(("key_up", "Control"), operations)
        finally:
            session.stop()

    def test_key_release_survives_resolution_change(self):
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.controller import connect_controller

        Toolkit.init_option(".")
        cfg = Config(jumpserver_url="http://127.0.0.1", display_selector="#remote",
                     connection_mode="cli", cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir=".", capture_mode="native_canvas",canvas_refresh_mode="browser")
        cfg.base_dir = Path(self.temp.name)
        session, controller = connect_controller(cfg)
        command = [self.node, str(self.cli), f"-s={self.session_name}", "--raw", "eval"]
        try:
            self.assertTrue(controller.post_click(120, 140).wait().succeeded)
            self.assertTrue(controller.post_key_down(17).wait().succeeded)
            result = subprocess.run(command + ["() => { document.querySelector('#surface').style.width = '1600px'; }"],
                                    cwd=self.temp.name, capture_output=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(controller.post_key_up(17).wait().succeeded)
        finally:
            subprocess.run(command + ["() => { document.querySelector('#surface').style.width = '1920px'; }"],
                           cwd=self.temp.name, capture_output=True, timeout=30)
            session.stop()


if __name__ == "__main__":
    unittest.main()
