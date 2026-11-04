"""Clipboard transport tests with a disposable local Guacamole-like page."""

import json
import os
from pathlib import Path
import subprocess
import unittest

import test_cli_controller


REMOTE = '''<!doctype html><html><body style="margin:0;overflow:hidden">
<div id="remote" style="width:960px;height:540px;overflow:hidden;position:relative">
<div style="width:1920px;height:1080px;transform:scale(.5);transform-origin:top left">
<canvas width="1920" height="1088" style="display:block"></canvas></div>
<textarea id="sink" style="position:fixed;width:0;height:0;border:0;padding:0"></textarea></div>
<div id="setting" style="position:absolute;left:100%;top:0;width:240px;height:400px">
<button style="margin:20px;width:190px;height:40px" onclick="document.querySelector('.el-drawer').style.display='block'">剪贴板</button></div>
<div class="el-drawer" style="display:none;position:absolute;left:0;top:0;width:460px;height:350px;background:white">
<textarea class="el-textarea__inner" style="width:420px;height:200px" oninput="window.remoteClipboard=this.value"></textarea>
<button aria-label="close 剪贴板" onclick="document.querySelector('.el-drawer').style.display='none'">Close</button></div>
<script>
window.settingsOpen=false;window.remoteClipboard='old';window.pasteCount=0;
window.toggleSettings=()=>{settingsOpen=!settingsOpen;document.querySelector('#setting').style.left=(settingsOpen?innerWidth-240:innerWidth)+'px';};
document.querySelector('#sink').addEventListener('keydown',e=>{
 if(e.ctrlKey&&e.key==='v'){e.preventDefault();window.received=window.remoteClipboard;window.pasteCount++;}
});
</script></body></html>'''


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_CLI'), 'CLI integration not enabled')
class JumpClipboardTests(unittest.TestCase):
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
        from psauto.controller import connect_controller

        Toolkit.init_option('.')
        outer = '''<iframe id="frame" style="width:1100px;height:650px;border:0"></iframe>
        <button onclick="document.querySelector('#frame').contentWindow.toggleSettings()">
        <nz-icon class="anticon-setting">settings</nz-icon></button>'''
        self.call('async (page)=>{await page.setViewportSize({width:1280,height:720});await page.setContent(' +
                  json.dumps(outer) + ');await page.locator("#frame").evaluate((el,html)=>el.srcdoc=html,' +
                  json.dumps(REMOTE) + ');await page.frameLocator("#frame").locator("#sink").focus();return true;}')
        cfg = Config(jumpserver_url=f'http://127.0.0.1:{self.server.server_port}', display_selector='#remote',
                     display_frame='#frame', connection_mode='cli', cli_session=self.session_name,
                     cli_script=str(self.cli), cli_workdir='.', capture_mode='native_canvas', text_input_mode='clipboard')
        cfg.base_dir = Path(self.temp.name)
        self.session, self.controller = connect_controller(cfg)

    def tearDown(self):
        self.session.stop()
        self.call('async (page)=>{await page.goto(' + json.dumps(f'http://127.0.0.1:{self.server.server_port}/native') +
                  ');return true;}')

    def test_multiline_unicode_payload_is_pasted_once_and_focus_is_restored(self):
        code = 'Local string &text;\r\n&text = "中文 $(literal) `data`";\r\n/* tab\tvalue */'
        self.assertTrue(self.controller.post_input_text(code).wait().succeeded)
        result = self.call('async (page)=>await page.frameLocator("#frame").locator("body").evaluate(()=>'
                           '({text:received,count:pasteCount,settings:settingsOpen,focus:document.activeElement.id}))')
        self.assertEqual(result['text'], code.replace('\r\n', '\n'))
        self.assertEqual(result['count'], 1)
        self.assertFalse(result['settings'])
        self.assertEqual(result['focus'], 'sink')

    def test_failed_clipboard_preparation_does_not_paste_old_content(self):
        self.call('async (page)=>{await page.frameLocator("#frame").locator("textarea.el-textarea__inner")'
                  '.evaluate(el=>el.readOnly=true);return true;}')
        with self.assertLogs('psauto.cli_controller', level='ERROR'):
            self.assertFalse(self.controller.post_input_text('new payload').wait().succeeded)
        self.assertEqual(self.call('async (page)=>await page.frameLocator("#frame").locator("body")'
                                  '.evaluate(()=>pasteCount)'), 0)

    def test_closed_tunnel_rejects_a_stale_canvas_and_remote_input(self):
        self.assertTrue(self.controller.post_key_down(17).wait().succeeded)
        self.call('''async page=>{
          await page.frameLocator('#frame').locator('#setting button').evaluate(el=>{
            el.__vue__={$options:{name:'GuacamoleConnect'},tunnel:{state:2},clientState:'Connected'};
            window.canvasClicks=0;
            document.querySelector('canvas').onclick=()=>window.canvasClicks++;
          });
          return true;
        }''')
        state = self.session.request('transport_state')
        self.assertTrue(state['known'])
        self.assertEqual(state['tunnel_state'], 2)
        with self.assertLogs('psauto.controller', level='ERROR'):
            self.assertFalse(self.controller.post_screencap().wait().succeeded)
        self.assertEqual(self.controller._held_keys, set())
        with self.assertLogs('psauto.cli_controller', level='ERROR'):
            self.assertFalse(self.controller.post_click(120,140).wait().succeeded)
            self.assertFalse(self.controller.post_input_text('must not paste').wait().succeeded)
        counters=self.call('async page=>await page.frameLocator("#frame").locator("body")'
                           '.evaluate(()=>({paste:pasteCount,click:canvasClicks}))')
        self.assertEqual(counters, {'paste':0,'click':0})

    def test_open_tunnel_does_not_use_the_legacy_connected_flag(self):
        self.call('''async page=>{
          await page.frameLocator('#frame').locator('#setting button').evaluate(el=>{
            el.__vue__={$options:{name:'GuacamoleConnect'},tunnel:{state:1},clientState:'Connected',connected:false};
          });
          return true;
        }''')
        self.assertTrue(self.controller.post_input_text('live tunnel').wait().succeeded)
        result=self.call('async page=>await page.frameLocator("#frame").locator("body")'
                         '.evaluate(()=>({text:received,count:pasteCount}))')
        self.assertEqual(result, {'text':'live tunnel','count':1})

    def test_leaving_drawer_finishes_before_the_next_canvas_click(self):
        self.call('''async page=>{
          await page.frameLocator('#frame').locator('body').evaluate(()=>{
            const drawer=document.querySelector('.el-drawer');
            const wrapper=document.createElement('div');
            wrapper.className='el-drawer__wrapper clipboardDrawer';
            wrapper.style.cssText='position:absolute;inset:0;z-index:10;display:none;opacity:1;transition:opacity 3s';
            drawer.before(wrapper);wrapper.append(drawer);
            document.querySelector('#setting button').onclick=()=>{
              wrapper.style.display='block';wrapper.style.opacity='1';drawer.style.display='block';
            };
            drawer.querySelector('button').onclick=()=>{wrapper.style.opacity='0';};
            wrapper.addEventListener('transitionend',()=>{
              if(wrapper.style.opacity==='0') wrapper.style.display='none';
            });
            document.querySelector('canvas').onclick=()=>{window.canvasClicked=true;};
          });
          return true;
        }''')
        self.assertTrue(self.controller.post_input_text('payload').wait().succeeded)
        self.assertTrue(self.controller.post_click(120, 140).wait().succeeded)
        self.assertTrue(self.call('async page=>await page.frameLocator("#frame").locator("body")'
                                  '.evaluate(()=>window.canvasClicked===true)'))
