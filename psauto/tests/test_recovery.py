"""Exercise real Maa OCR and CLI clicks against a disposable local recovery page."""

import json
import os
from pathlib import Path
import subprocess
import unittest

import test_cli_controller


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_CLI') and os.environ.get('PSAUTO_TEST_OCR'),
                     'CLI/OCR integration not enabled')
class RecoveryCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_cli_controller.CliControllerTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        test_cli_controller.CliControllerTests.tearDownClass.__func__(cls)

    def call(self, code):
        result = subprocess.run([self.node, str(self.cli), f'-s={self.session_name}', '--raw', 'run-code', code],
                                cwd=self.temp.name, capture_output=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def setUp(self):
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.recovery import connect_recovery_controller

        Toolkit.init_option('.')
        self.call('async (page) => { await page.setViewportSize({width:1920,height:1024}); return true; }')
        self.base_url = f'http://127.0.0.1:{self.server.server_port}'
        self.cfg = Config(jumpserver_url=self.base_url,
                          display_selector='#remote', connection_mode='cli', cli_session=self.session_name,
                          cli_script=str(self.cli), cli_workdir='.', capture_mode='native_canvas')
        self.cfg.base_dir = Path(self.temp.name)
        self.session, self.controller = connect_recovery_controller(self.cfg)

    def tearDown(self):
        self.session.stop()
        self.call('async (page) => { await page.goto(' + json.dumps(self.base_url + '/native') +
                  '); return true; }')

    def tasker(self):
        from psauto.pipeline import create_tasker
        return create_tasker(str(Path(__file__).resolve().parents[2] / 'assets/resource'), self.controller)

    def show_dialog(self, message):
        html = '''<div style="position:absolute;left:749px;top:444px;width:422px;height:136px;
        background:white;color:#333;font:14px Microsoft YaHei,Arial,sans-serif">
        <div style="position:absolute;left:15px;top:14px;font-size:18px">连接异常</div>
        <div style="position:absolute;left:15px;top:58px">''' + message + '''</div>
        <button onclick="document.body.dataset.clicks='1';this.parentElement.remove()"
        style="position:absolute;left:350px;top:93px;width:56px;height:32px;
        border:0;background:#409eff;color:white">确定</button></div>'''
        self.call('async (page) => { await page.evaluate(html=>{document.body.innerHTML=html;'
                  'document.body.style.background="#111";delete document.body.dataset.clicks;},' +
                  json.dumps(html) + '); return true; }')

    def test_unknown_error_stops_and_real_idle_text_clicks(self):
        tasker = self.tasker()
        self.show_dialog('服务器维护，请联系管理员')
        failed = tasker.post_task('JumpServer_AcknowledgeIdleTimeout',
                                  {'JumpServer_AcknowledgeIdleTimeout': {'timeout': 400}}).wait()
        self.assertFalse(failed.succeeded)
        self.assertIsNone(self.call('async (page) => await page.evaluate(()=>document.body.dataset.clicks||null)'))
        self.show_dialog('超过最大空闲时间120分钟，断开连接')
        succeeded = tasker.post_task('JumpServer_AcknowledgeIdleTimeout').wait()
        self.assertTrue(succeeded.succeeded)
        self.assertEqual(self.call('async (page) => await page.evaluate(()=>document.body.dataset.clicks)'), '1')

    def test_resize_after_capture_and_wrong_origin_refuse_clicks(self):
        shot = self.controller.post_screencap().wait()
        self.assertTrue(shot.succeeded)
        self.assertEqual(shot.get().shape, (1080, 1920, 3))
        self.call('async (page) => {await page.setViewportSize({width:1900,height:1000}); return true;}')
        self.assertFalse(self.controller.post_click(100, 100).wait().succeeded)
        self.call('async (page) => {await page.setViewportSize({width:1920,height:900}); return true;}')
        self.assertFalse(self.controller.post_click(100, 100).wait().succeeded)
        self.cfg.jumpserver_url = 'http://different.invalid'
        self.assertFalse(self.controller.post_click(100, 100).wait().succeeded)

    def test_reload_accepts_only_beforeunload(self):
        self.call('async (page) => {await page.mouse.click(10,10); await page.evaluate(()=>'
                  'addEventListener("beforeunload",e=>{e.preventDefault(); e.returnValue="";})); return true;}')
        tasker = self.tasker()
        job = tasker.post_task('JumpServer_ReloadSession',
                               {'JumpServer_ReloadSession': {'next': [], 'post_delay': 100}}).wait()
        self.assertTrue(job.succeeded)
        self.assertEqual(self.call('async (page) => await page.locator("#native").count()'), 1)

    def test_saved_account_connect_uses_ocr_button(self):
        html = '''<div style="position:absolute;left:600px;top:150px;color:#111;background:white;
        width:720px;height:600px;font:20px Microsoft YaHei,Arial,sans-serif">
        <p>连接 - PS开发测试</p><p>RDP</p><p>用户名</p><p>密码</p><p>Web GUI</p>
        <div style="position:absolute;left:530px;top:270px">记住密码</div>
        <button onclick="document.body.dataset.connected='yes'" style="position:absolute;
        left:20px;top:530px;width:660px;height:36px;font:16px Microsoft YaHei;
        color:white;background:#12b99a;border:0">连接(当前在线:0)</button></div>'''
        self.call('async (page) => {await page.evaluate(html=>{document.body.innerHTML=html;},' +
                  json.dumps(html) + '); return true;}')
        job = self.tasker().post_task('JumpServer_Recover').wait()
        self.assertTrue(job.succeeded)
        self.assertEqual(self.call('async (page) => await page.evaluate(()=>document.body.dataset.connected)'), 'yes')
