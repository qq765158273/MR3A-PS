"""Compare baseline/current CLI on one page, alternating order each round.

Default: READ ONLY on the configured business page. --isolated launches a local
test page and checks asynchronous pixels, key/click counts and clipboard input.
No business actions are sent in the default mode. Uses the installed official CLI.
"""
import argparse
from contextlib import ExitStack
import hashlib
import http.server
import importlib.util
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import uuid

import numpy as np

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from psauto.cli_controller import PlaywrightCliSession
from psauto.config import load_config
from psauto.native_canvas import decode_canvas


def summary(rows):
    result = {}
    for label in ('baseline', 'current'):
        selected = [row for row in rows if row['implementation'] == label]
        result[label] = {}
        for key in sorted({key for row in selected for key in row if key.endswith('_ms')}):
            values = sorted(row[key] for row in selected if key in row)
            result[label][key] = {'count':len(values), 'median_ms':statistics.median(values),
                                  'p95_ms':values[math.ceil(len(values)*.95)-1], 'max_ms':max(values)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=BASE/'config.json')
    parser.add_argument('--baseline-ref', default='66196b3')
    parser.add_argument('--samples', type=int, default=12)
    parser.add_argument('--isolated', action='store_true')
    args = parser.parse_args()
    cfg = load_config(args.config)
    cfg.text_input_mode = 'clipboard'
    with ExitStack() as stack:
        tmp = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        # Save exact baseline files together: __file__ resolves its own worker.
        sources = {}
        for filename in ('cli_controller.py', 'cli_worker.cjs'):
            source = subprocess.check_output(['git','show',f'{args.baseline_ref}:psauto/psauto/{filename}'],cwd=BASE.parent)
            (tmp/filename).write_bytes(source)
            sources[filename] = hashlib.sha256(source).hexdigest()
        spec = importlib.util.spec_from_file_location('psauto._baseline_cli', tmp/'cli_controller.py')
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        if args.isolated:
            sys.path.insert(0,str(BASE/'tests'))
            from test_browser_session import Handler
            from test_jump_clipboard import REMOTE
            server = http.server.ThreadingHTTPServer(('127.0.0.1',0), Handler)
            threading.Thread(target=server.serve_forever,daemon=True).start()
            stack.callback(server.server_close)
            stack.callback(server.shutdown)
            cfg.cli_session = 'psauto-batch-'+uuid.uuid4().hex[:10]
            cli = cfg.resolve_path(cfg.cli_script).resolve()
            cfg.cli_workdir = str(tmp)
            config = tmp/'cli.json'
            config.write_text(json.dumps({'timeouts':{'settle':0},'browser':{'launchOptions':{'headless':True}}}),encoding='utf-8')
            command = ['node',str(cli),f'-s={cfg.cli_session}']
            result = subprocess.run(command+['open',f'http://127.0.0.1:{server.server_port}/native','--browser=chrome',f'--config={config}'],cwd=tmp,capture_output=True,timeout=60)
            if result.returncode: raise RuntimeError('Disposable CLI browser failed to open')
            stack.callback(lambda: subprocess.run(command+['close'],cwd=tmp,capture_output=True,timeout=30))
            cfg.display_frame = '#frame'
            cfg.display_selector = '#remote'
            cfg.canvas_refresh_mode = 'guacamole'
            cfg.cli_settle_ms = 0
        sessions = {'baseline': baseline.PlaywrightCliSession(cfg), 'current': PlaywrightCliSession(cfg)}
        for session in sessions.values():
            stack.callback(session.stop)
            session.run_code('async page=>true')
        active = sessions['current']
        if args.isolated:
            active.run_code('''async page=>{
              await page.setViewportSize({width:1280,height:720});
              await page.setContent('<iframe id="frame" style="width:1100px;height:650px;border:0"></iframe>');
              await page.locator('#frame').evaluate((el,html)=>el.srcdoc=html,__HTML__);
              await page.frameLocator('#frame').locator('#sink').focus();
              await page.frameLocator('#frame').locator('#setting button').evaluate(el=>{
                window.revision=0;window.pending=[];window.clicks=0;
                document.querySelector('canvas').onclick=()=>{clicks++;document.querySelector('#sink').focus();};
                document.querySelector('#sink').addEventListener('keydown',e=>{
                  if(e.key==='Enter'){
                    const revision=++window.revision;
                    window.pending.push(new Promise(resolve=>setTimeout(()=>{
                      const ctx=document.querySelector('canvas').getContext('2d');
                      ctx.fillStyle=`rgb(${revision},10,20)`;ctx.fillRect(100,100,30,30);resolve();
                    },35)));
                  }
                });
                el.__vue__={$options:{name:'GuacamoleConnect'},tunnel:{state:1},clientState:'Connected',
                  client:{getDisplay:()=>({getWidth:()=>1920,getHeight:()=>1080,
                    flush:done=>Promise.all(window.pending.splice(0)).then(done)})}};
              });return true;
            }'''.replace('__HTML__',json.dumps(REMOTE)))
        browser = active.run_code('async page=>page.evaluate(()=>({visibility:document.visibilityState,width:innerWidth,height:innerHeight,dpr:devicePixelRatio}))')
        rows, pixel_pairs, revision = [], [], 0
        for index in range(args.samples):
            pair = {}
            order = ['baseline','current'] if index%2==0 else ['current','baseline']
            for label in order:
                session = sessions[label]
                row = {'implementation':label,'round':index}
                started = time.perf_counter()
                assert session.request('inspect') is True
                row['inspect_ms'] = (time.perf_counter()-started)*1000
                if args.isolated:
                    started = time.perf_counter()
                    assert session.request('key',key='Enter') is True
                    row['key_ms'] = (time.perf_counter()-started)*1000
                    revision += 1
                started = time.perf_counter()
                info = session.request('screencap')
                row['capture_cli_ms'] = (time.perf_counter()-started)*1000
                row['profile'] = session.timings[-1]
                started = time.perf_counter()
                pixels = decode_canvas(info,cfg)
                row['decode_ms'] = (time.perf_counter()-started)*1000
                row['capture_total_ms'] = row['capture_cli_ms']+row['decode_ms']
                assert pixels.shape == (1080,1920,3)
                pair[label] = pixels
                if args.isolated:
                    assert pixels[110,110].tolist() == [20,10,revision]
                    started = time.perf_counter()
                    assert session.request('click',x=120,y=140) is True
                    row['click_ms'] = (time.perf_counter()-started)*1000
                rows.append(row)
            if not args.isolated:
                pixel_pairs.append(bool(np.array_equal(pair['baseline'],pair['current'])))
        if args.isolated:
            for session in sessions.values():
                assert session.request('input_text',text='Local string &s;\n&s="中文 $(literal)";',clipboard=True) is True
            state = active.run_code('async page=>page.frameLocator("#frame").locator("body").evaluate(()=>({revision,clicks,pastes:pasteCount}))')
            assert state == {'revision':2*args.samples,'clicks':2*args.samples,'pastes':2},state
        else:
            state = {'equal_pixel_pairs':sum(pixel_pairs),'compared_pixel_pairs':len(pixel_pairs)}
        result = {'mode':'isolated' if args.isolated else 'live_readonly','browser':browser,
                  'baseline_ref':args.baseline_ref,'baseline_source_sha256':sources,
                  'current_source_sha256':hashlib.sha256((BASE/'psauto/cli_controller.py').read_bytes()).hexdigest(),
                  'cli_settings':{label:session.cli_settings for label,session in sessions.items()},
                  'summary':summary(rows),'state':state,'measurements':rows}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({key:result[key] for key in ('mode','browser','summary','state')},indent=2))


if __name__ == '__main__': main()
