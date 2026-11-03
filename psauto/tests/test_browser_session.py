import contextlib
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from psauto.config import Config
from psauto.session import BrowserSession, display, open_remote


DISPLAY_HTML = b"""<!doctype html><html><head><style>
body { margin: 0; }
#remote { position: absolute; left: 30px; top: 40px; width: 120px; height: 80px;
          background: rgb(240, 10, 20); outline: none; }
</style></head><body><div id="remote" tabindex="0"
onclick="this.dataset.click = (event.clientX - 30) + ',' + (event.clientY - 40)"
onkeydown="this.dataset.key = event.key"></div></body></html>"""

OCR_HTML = b"""<!doctype html><html><body style="margin:0">
<div id="remote" onclick="this.dataset.click = 'yes'" style="width:600px;height:120px;background:white;color:black;
font:32px Arial,sans-serif;padding:12px;box-sizing:border-box">Open Definition</div>
</body></html>"""

CANVAS_HTML = b"""<!doctype html><html><body style="margin:0">
<div id="remote" onclick="this.dataset.click = (event.clientX - 30) + ',' + (event.clientY - 40)"
style="position:absolute;left:30px;top:40px;width:120px;height:80px">
<canvas id="base" width="120" height="80" style="position:absolute"></canvas>
<canvas id="overlay" width="120" height="80" style="position:absolute"></canvas></div>
<script>
let base = document.getElementById('base').getContext('2d');
base.fillStyle = 'rgb(240,10,20)'; base.fillRect(0, 0, 120, 80);
let overlay = document.getElementById('overlay').getContext('2d');
overlay.fillStyle = 'rgb(0,230,40)'; overlay.fillRect(5, 5, 25, 25);
</script></body></html>"""

NATIVE_HTML = b"""<!doctype html><html><body style="margin:0">
<div id="remote" style="position:absolute;left:30px;top:40px;width:960px;height:540px;overflow:hidden">
<div id="surface" style="width:1920px;height:1080px;transform:scale(.5);transform-origin:top left;overflow:hidden">
<canvas id="native" tabindex="0" width="1920" height="1088" style="display:block"></canvas></div></div>
<script>
const canvas = document.querySelector('#native'), ctx = canvas.getContext('2d');
ctx.fillStyle='rgb(240,10,20)'; ctx.fillRect(0,0,1920,1080);
ctx.fillStyle='rgb(0,230,40)'; ctx.fillRect(100,100,80,80);
ctx.fillStyle='blue'; ctx.fillRect(0,1080,1920,8);
ctx.fillStyle='white'; ctx.fillRect(0,0,900,70);
ctx.fillStyle='black'; ctx.font='32px Arial'; ctx.fillText('Application Designer - HRDEV', 10, 45);
canvas.addEventListener('click', e => {
  const r=canvas.getBoundingClientRect();
  document.body.dataset.point = Math.round((e.clientX-r.left)*canvas.width/r.width) + ',' +
    Math.round((e.clientY-r.top)*canvas.height/r.height);
});
canvas.addEventListener('mousedown', () => { document.body.dataset.drag='down'; });
canvas.addEventListener('mouseup', () => { document.body.dataset.drag='up'; });
</script></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/popup":
            content = b"<button id='open' onclick=\"window.open('/display')\">Open</button>"
        elif self.path == "/popup-step":
            content = b"<button id='open' onclick=\"window.open('/step2')\">Open</button>"
        elif self.path == "/step2":
            content = b"<button id='continue' onclick=\"location.href='/display'\">Continue</button>"
        elif self.path == "/frame":
            content = b"<iframe id='frame' src='/display' style='margin:25px;width:250px;height:180px'></iframe>"
        elif self.path == "/ocr":
            content = OCR_HTML
        elif self.path == "/canvas":
            content = CANVAS_HTML
        elif self.path == "/native":
            content = NATIVE_HTML
        elif self.path == "/native-frame":
            content = b"<iframe id='frame' src='/native' style='margin:25px;width:1100px;height:650px'></iframe>"
        else:
            content = DISPLAY_HTML
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass


@unittest.skipUnless(os.environ.get("PSAUTO_TEST_BROWSER_CHANNEL"), "browser integration not enabled")
class BrowserSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join()

    def setUp(self):
        self.cfg = Config(jumpserver_url=self.base, connect_url=self.base + "/display",
                          display_selector="#remote", browser_channel=os.environ["PSAUTO_TEST_BROWSER_CHANNEL"])
        self.session = BrowserSession(self.cfg)
        self.session.start()

    def tearDown(self):
        self.session.stop()

    def test_screenshot_click_and_keyboard(self):
        from psauto.imaging import png_to_bgr

        open_remote(self.session, self.cfg)
        image = png_to_bgr(self.session.call(lambda page: display(page, self.cfg).screenshot()))
        self.assertEqual(image.shape, (80, 120, 3))
        self.assertEqual(image[10, 10].tolist(), [20, 10, 240])
        self.session.call(lambda page: page.mouse.click(40, 55))
        self.session.call(lambda page: page.keyboard.press("Enter"))
        click, key = self.session.call(lambda page: page.locator("#remote").evaluate(
            "el => [el.dataset.click, el.dataset.key]"))
        self.assertEqual(click, "10,15")
        self.assertEqual(key, "Enter")

    def test_display_can_open_in_popup(self):
        self.cfg.connect_url = self.base + "/popup"
        self.cfg.pre_connect_clicks = ["#open"]
        open_remote(self.session, self.cfg)
        self.assertTrue(self.session.call(lambda page: page.url.endswith("/display")))

    def test_connection_steps_can_continue_in_popup(self):
        self.cfg.connect_url = self.base + "/popup-step"
        self.cfg.pre_connect_clicks = ["#open", "#continue"]
        self.session.call(lambda page: page.set_default_timeout(1000))
        open_remote(self.session, self.cfg)
        self.assertTrue(self.session.call(lambda page: page.url.endswith("/display")))

    def test_maa_controller_coordinates_inside_iframe(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/frame"
        self.cfg.display_frame = "#frame"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        self.assertEqual(controller.post_screencap().wait().get().shape, (80, 120, 3))
        self.assertTrue(controller.post_click(10, 15).wait().succeeded)
        click = self.session.call(lambda page: page.frame_locator("#frame").locator("#remote").get_attribute("data-click"))
        self.assertEqual(click, "10,15")

    def test_maa_screenshot_composes_canvas_layers(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/canvas"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        image = controller.post_screencap().wait().get()
        self.assertEqual(image.shape, (80, 120, 3))
        self.assertEqual(image[10, 10].tolist(), [40, 230, 0])
        self.assertEqual(image[40, 60].tolist(), [20, 10, 240])
        self.assertTrue(controller.post_click(10, 15).wait().succeeded)
        self.assertEqual(self.session.call(lambda page: page.locator("#remote").get_attribute("data-click")), "10,15")

    def test_native_canvas_screenshot_and_scaled_click_in_iframe(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/native-frame"
        self.cfg.display_frame = "#frame"
        self.cfg.capture_mode = "native_canvas"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        job = controller.post_screencap().wait()
        self.assertTrue(job.succeeded)
        image = job.get()
        self.assertEqual(image.shape, (1080, 1920, 3))
        self.assertEqual(image[120, 120].tolist(), [40, 230, 0])
        self.assertEqual(image[1079, 100].tolist(), [20, 10, 240])
        self.assertTrue(controller.post_click(120, 140).wait().succeeded)
        point = self.session.call(lambda page: page.frame_locator("#frame").locator("body").get_attribute("data-point"))
        self.assertEqual(point, "120,140")

    def test_native_canvas_composes_small_translated_layer_and_rejects_unknown_overlay(self):
        from psauto.native_canvas import capture_native

        self.cfg.connect_url = self.base + '/native'
        self.cfg.capture_mode = 'native_canvas'
        open_remote(self.session, self.cfg)
        self.session.call(lambda page: page.evaluate('''() => {
            const screen=document.querySelector('#surface'), canvas=document.querySelector('#native');
            const desktop=document.createElement('div');
            desktop.style='width:1920px;height:1080px;position:absolute;left:0;top:0;overflow:hidden';
            screen.appendChild(desktop);desktop.appendChild(canvas);
            const layer=document.createElement('div');layer.id='cursor-layer';
            layer.style='width:41px;height:39px;position:absolute;left:0;top:0;overflow:hidden;transform:translate(300px,200px)';
            const cursor=document.createElement('canvas');cursor.width=64;cursor.height=64;
            cursor.style='position:absolute;left:0;top:0';
            const ctx=cursor.getContext('2d');ctx.fillStyle='rgb(255,0,255)';ctx.fillRect(0,0,8,8);
            layer.appendChild(cursor);screen.appendChild(layer);
        }'''))
        image = self.session.call(lambda page: capture_native(page, self.cfg))
        self.assertEqual(image.shape, (1080, 1920, 3))
        self.assertEqual(image[204, 304].tolist(), [255, 0, 255])
        self.assertEqual(image[120, 120].tolist(), [40, 230, 0])
        self.session.call(lambda page: page.locator('#cursor-layer').evaluate("el=>el.style.transform='rotate(30deg)'"))
        with self.assertRaises(Exception):
            self.session.call(lambda page: capture_native(page, self.cfg))
        self.session.call(lambda page: page.locator('#cursor-layer').evaluate("el=>{el.style.transform='translate(300px,200px)';el.firstElementChild.width=128;}"))
        with self.assertRaises(Exception):
            self.session.call(lambda page: capture_native(page, self.cfg))

    def test_native_canvas_rejects_resolution_change_and_multiple_layers(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/native"
        self.cfg.capture_mode = "native_canvas"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        self.session.call(lambda page: page.locator("#surface").evaluate("el => el.style.width='1600px'"))
        with self.assertLogs("psauto.controller", level="ERROR"):
            self.assertFalse(controller.click(120, 140))
        with self.assertLogs("psauto.controller", level="ERROR"):
            self.assertTrue(controller.post_screencap().wait().failed)
        self.session.call(lambda page: page.locator("#surface").evaluate("el => { el.style.width='1920px'; el.appendChild(document.createElement('canvas')); }"))
        with self.assertLogs("psauto.controller", level="ERROR"):
            self.assertFalse(controller.click(120, 140))
        self.assertIsNone(self.session.call(lambda page: page.locator("body").get_attribute("data-point")))

    def test_native_canvas_rejects_overlay(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/native"
        self.cfg.capture_mode = "native_canvas"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.post_connection().wait().succeeded)
        self.session.call(lambda page: page.evaluate("""() => {
            const overlay=document.createElement('div');
            overlay.style='position:absolute;left:30px;top:40px;width:100px;height:100px;z-index:999';
            document.body.appendChild(overlay);
        }"""))
        with self.assertLogs("psauto.controller", level="ERROR"):
            self.assertFalse(controller.click(120, 140))
        self.assertIsNone(self.session.call(lambda page: page.locator("body").get_attribute("data-point")))

    @unittest.skipUnless(os.environ.get("PSAUTO_TEST_OCR"), "OCR integration not enabled")
    def test_pside_ready_pipeline_on_native_canvas(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController
        from psauto.pipeline import create_tasker

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/native"
        self.cfg.capture_mode = "native_canvas"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            source = Path(__file__).resolve().parents[2] / "assets/resource/pipeline/PSIDE/ready.json"
            (bundle / "pipeline").mkdir()
            shutil.copy(source, bundle / "pipeline/pside_ready.json")
            (bundle / "default_pipeline.json").write_text(
                json.dumps({"Default": {"on_error": "Default_on_error"}}), encoding="utf-8")
            (bundle / "pipeline/default.json").write_text(
                json.dumps({"Default_on_error": {}}), encoding="utf-8")
            model = Path(__file__).resolve().parents[2] / "assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn"
            shutil.copytree(model, bundle / "model/ocr")
            tasker = create_tasker(str(bundle), controller)
            job = tasker.post_task("PSIDE_WindowReady").wait()
            self.assertTrue(job.succeeded)
            self.assertTrue(job.get().nodes[0].recognition.hit)
            self.session.call(lambda page: page.locator("#native").evaluate(
                "c => { const ctx=c.getContext('2d'); ctx.fillStyle='white'; ctx.fillRect(0,0,900,70); }"))
            failed = tasker.post_task("PSIDE_WindowReady", {"PSIDE_WindowReady": {"timeout": 200}}).wait()
            self.assertTrue(failed.failed)

    def test_storage_state_is_restored_in_new_session(self):
        self.session.call(lambda page: page.goto(self.base + "/display"))
        self.session.call(lambda page: page.evaluate("localStorage.setItem('test-session', 'present')"))
        with tempfile.TemporaryDirectory() as tmp:
            self.cfg.storage_state = str(Path(tmp) / "state.json")
            self.session.save_storage_state()
            other = BrowserSession(self.cfg)
            other.start()
            try:
                other.call(lambda page: page.goto(self.base + "/display"))
                self.assertEqual(other.call(lambda page: page.evaluate("localStorage.getItem('test-session')")), "present")
            finally:
                other.stop()

    def test_login_and_discover_commands(self):
        import runner

        self.cfg.jumpserver_url = self.base + "/canvas"
        interactive_session = []

        def make_session(cfg):
            cfg.headless = True
            session = BrowserSession(cfg)
            interactive_session.append(session)
            return session

        def complete_login(prompt):
            interactive_session[-1].call(lambda page: page.evaluate("localStorage.setItem('login', 'ok')"))
            return ""

        with tempfile.TemporaryDirectory() as tmp:
            self.cfg.storage_state = str(Path(tmp) / "state.json")
            with patch.object(runner, "BrowserSession", side_effect=make_session), \
                 patch("builtins.input", side_effect=complete_login), \
                 contextlib.redirect_stdout(io.StringIO()):
                runner.cmd_login(self.cfg, None)
            state = json.loads(Path(self.cfg.storage_state).read_text(encoding="utf-8"))
            self.assertEqual(state["origins"][0]["localStorage"][0]["value"], "ok")

            output = io.StringIO()
            with patch.object(runner, "BrowserSession", side_effect=make_session), \
                 patch("builtins.input", return_value=""), contextlib.redirect_stdout(output):
                runner.cmd_discover(self.cfg, None)
            pages = json.loads(output.getvalue())
            self.assertEqual(len(pages[0]["canvases"]), 2)
            self.assertEqual(pages[0]["canvases"][0]["width"], 120)

    def test_timed_out_queued_work_does_not_execute(self):
        open_remote(self.session, self.cfg)
        started = threading.Event()

        def block(page):
            started.set()
            time.sleep(0.4)

        worker = threading.Thread(target=lambda: self.session.call(block))
        worker.start()
        self.assertTrue(started.wait(timeout=2))
        with self.assertRaisesRegex(TimeoutError, "queued operation cancelled"):
            self.session.call(lambda page: page.evaluate("window.unexpected = true"), timeout=0.05)
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        self.assertIsNone(self.session.call(lambda page: page.evaluate("window.unexpected")))

    def test_timeout_from_operation_is_preserved(self):
        def fail(page):
            raise TimeoutError("original error")

        with self.assertRaisesRegex(TimeoutError, "original error"):
            self.session.call(fail)

    def test_running_timeout_rejects_subsequent_queued_work(self):
        started = threading.Event()
        executed = threading.Event()
        failures = []

        def slow(page):
            started.set()
            time.sleep(0.5)

        def run_slow():
            try:
                self.session.call(slow, timeout=0.15)
            except Exception as exc:
                failures.append(exc)

        def run_queued():
            try:
                self.session.call(lambda page: executed.set(), timeout=2)
            except Exception as exc:
                failures.append(exc)

        running = threading.Thread(target=run_slow)
        running.start()
        self.assertTrue(started.wait(timeout=2))
        queued = threading.Thread(target=run_queued)
        queued.start()
        running.join(timeout=2)
        queued.join(timeout=2)
        self.assertFalse(running.is_alive())
        self.assertFalse(queued.is_alive())
        self.assertFalse(executed.is_set())
        self.assertTrue(any(isinstance(exc, TimeoutError) for exc in failures))
        self.assertTrue(any(isinstance(exc, RuntimeError) for exc in failures))
        with self.assertRaises(RuntimeError):
            self.session.call(lambda page: None)

    def test_maa_controller_screenshot_and_input(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        image_job = controller.post_screencap().wait()
        self.assertTrue(image_job.succeeded)
        image = image_job.get()
        self.assertEqual(image.shape, (80, 120, 3))
        self.assertEqual(image[10, 10].tolist(), [20, 10, 240])
        self.assertTrue(controller.post_click(10, 15).wait().succeeded)
        self.assertTrue(controller.post_click_key(13).wait().succeeded)
        click, key = self.session.call(lambda page: page.locator("#remote").evaluate(
            "el => [el.dataset.click, el.dataset.key]"))
        self.assertEqual(click, "10,15")
        self.assertEqual(key, "Enter")
        with self.assertLogs("psauto.controller", level="ERROR"):
            self.assertFalse(controller.click(-1, 1))

    def test_maa_controller_reports_screenshot_failure(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController

        Toolkit.init_option(".")
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        self.session.call(lambda page: page.close())
        with self.assertLogs("psauto.controller", level="ERROR"):
            self.assertTrue(controller.post_screencap().wait().failed)

    def test_maa_pipeline_calls_native_key(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController
        from psauto.pipeline import create_tasker

        Toolkit.init_option(".")
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        self.assertTrue(controller.post_click(10, 15).wait().succeeded)
        with tempfile.TemporaryDirectory() as tmp:
            pipeline = Path(tmp) / "pipeline"
            pipeline.mkdir()
            (pipeline / "test.json").write_text(json.dumps({
                "LocalKey": {
                    "recognition": {"type": "DirectHit"},
                    "action": {"type": "ClickKey", "param": {"key": 13}}
                }
            }), encoding="utf-8")
            tasker = create_tasker(tmp, controller)
            job = tasker.post_task("LocalKey").wait()
            self.assertTrue(job.succeeded)
        self.assertEqual(self.session.call(lambda page: page.locator("#remote").get_attribute("data-key")), "Enter")

    def test_maa_pipeline_matches_and_clicks_template(self):
        from maa.toolkit import Toolkit
        from PIL import Image
        from psauto.controller import JumpServerController
        from psauto.pipeline import create_tasker

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/ocr"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        image = controller.post_screencap().wait().get()
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "pipeline").mkdir()
            (bundle / "image").mkdir()
            Image.fromarray(image[:, :, ::-1]).crop((8, 8, 250, 56)).save(bundle / "image" / "text.png")
            (bundle / "pipeline" / "test.json").write_text(json.dumps({
                "LocalTemplate": {"recognition": {"type": "TemplateMatch",
                    "param": {"template": ["text.png"], "threshold": 0.9}},
                    "action": {"type": "Click"}, "timeout": 5000}
            }), encoding="utf-8")
            tasker = create_tasker(tmp, controller)
            self.assertTrue(tasker.post_task("LocalTemplate").wait().succeeded)
        self.assertEqual(self.session.call(lambda page: page.locator("#remote").get_attribute("data-click")), "yes")

    def test_capture_command_and_failure_exit_code(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(json.dumps({"jumpserver_url": self.base,
                "connect_url": self.base + "/display", "display_selector": "#remote",
                "browser_channel": os.environ["PSAUTO_TEST_BROWSER_CHANNEL"]}), encoding="utf-8")
            runner = Path(__file__).resolve().parents[1] / "runner.py"
            command = [sys.executable, str(runner), "capture", "--config", str(config_path)]
            other_cwd = Path(tmp) / "other-cwd"
            other_cwd.mkdir()
            success = subprocess.run(command + ["--click", "10,15"], cwd=other_cwd, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            with Image.open(Path(tmp) / "out/capture.png") as image:
                self.assertEqual(image.size, (120, 80))
            self.assertFalse((other_cwd / "out").exists())
            self.assertFalse((other_cwd / "debug").exists())
            failure = subprocess.run(command + ["--click", "-1,15"], cwd=tmp, capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)

    def test_pipeline_command_and_failure_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "resource"
            (bundle / "pipeline").mkdir(parents=True)
            (bundle / "pipeline" / "test.json").write_text(json.dumps({
                "Smoke": {"recognition": {"type": "DirectHit"}}
            }), encoding="utf-8")
            config_path = Path(tmp) / "config.json"
            config_path.write_text(json.dumps({"jumpserver_url": self.base,
                "connect_url": self.base + "/display", "display_selector": "#remote",
                "browser_channel": os.environ["PSAUTO_TEST_BROWSER_CHANNEL"],
                "resource_dir": str(bundle)}), encoding="utf-8")
            runner = Path(__file__).resolve().parents[1] / "run_pipeline.py"
            command = [sys.executable, str(runner), "Smoke", "--config", str(config_path)]
            other_cwd = Path(tmp) / "other-cwd"
            other_cwd.mkdir()
            success = subprocess.run(command, cwd=other_cwd, capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertTrue((Path(tmp) / "out/after_run.png").is_file())
            self.assertFalse((other_cwd / "debug").exists())
            command[2] = "MissingNode"
            failure = subprocess.run(command, cwd=tmp, capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)

    def test_probe_saves_three_screenshots(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(json.dumps({"jumpserver_url": self.base,
                "connect_url": self.base + "/display", "display_selector": "#remote",
                "browser_channel": os.environ["PSAUTO_TEST_BROWSER_CHANNEL"]}), encoding="utf-8")
            runner = Path(__file__).resolve().parents[1] / "runner.py"
            result = subprocess.run([sys.executable, str(runner), "probe", "--config", str(config_path)],
                                    cwd=tmp, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            for index in range(3):
                with Image.open(Path(tmp) / "out" / f"probe_{index}.png") as image:
                    self.assertEqual(image.size, (120, 80))

    @unittest.skipUnless(os.environ.get("PSAUTO_TEST_OCR"), "OCR integration not enabled")
    def test_maa_ocr_with_repository_model(self):
        from maa.toolkit import Toolkit
        from psauto.controller import JumpServerController
        from psauto.pipeline import create_tasker

        Toolkit.init_option(".")
        self.cfg.connect_url = self.base + "/ocr"
        open_remote(self.session, self.cfg)
        controller = JumpServerController(self.session, self.cfg)
        self.assertTrue(controller.set_screenshot_use_raw_size(True))
        self.assertTrue(controller.post_connection().wait().succeeded)
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp)
            (bundle / "pipeline").mkdir()
            (bundle / "pipeline" / "test.json").write_text(json.dumps({
                "LocalOCR": {"recognition": {"type": "OCR", "param": {"expected": ["Open Definition"]}},
                             "timeout": 5000}
            }), encoding="utf-8")
            model = Path(__file__).resolve().parents[2] / "assets/MaaCommonAssets/OCR/ppocr_v5/zh_cn"
            shutil.copytree(model, bundle / "model/ocr")
            tasker = create_tasker(tmp, controller)
            job = tasker.post_task("LocalOCR").wait()
            self.assertTrue(job.succeeded)
