"""Native Maa regression checks for similar counters and Step numbers; no browser."""
import json
import os
from pathlib import Path
import unittest

import numpy as np
from PIL import Image, ImageDraw, ImageFont


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_OCR'), 'Native vision integration not enabled')
class ImageRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from maa.define import LoggingLevelEnum
        from maa.tasker import Tasker
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.controller import JumpServerController
        from psauto.pipeline import create_tasker

        class ImageController(JumpServerController):
            frame = np.zeros((1080,1920,3), dtype=np.uint8)
            click_hook = None
            key_hook = None
            def connect(self): return True
            def connected(self): return True
            def request_uuid(self): return 'offline-vision-regression'
            def screencap(self): return self.frame.copy()
            def reject_input(self,*args): raise AssertionError('Offline test cannot send input')
            def click(self, x, y):
                if self.click_hook is None:
                    return self.reject_input(x, y)
                return self.click_hook(x, y)
            def click_key(self,key):
                return self.key_hook(key) if self.key_hook else self.reject_input(key)
            key_down = key_up = input_text = reject_input

        cls.base = Path(__file__).resolve().parents[1]
        cls.fixtures = cls.base/'tests/fixtures/vision'
        cls.resource = cls.base.parent/'assets/resource'
        Toolkit.init_option(str(cls.base))
        Tasker.set_stdout_level(LoggingLevelEnum.Off)
        cls.controller = ImageController(None, Config(jumpserver_url='http://offline.invalid'))
        cls.controller.set_screenshot_use_raw_size(True)
        assert cls.controller.post_connection().wait().succeeded
        cls.tasker = create_tasker(str(cls.resource),cls.controller)

    def image(self,name):
        return Image.open(self.fixtures/name).convert('RGB')

    def test_build_requires_exact_record_error_and_warning_counts_before_closing(self):
        crop=self.image('build_success_feedback.png')
        font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
        cases=[('captured',None,True),("synthetic-success",(1,0,0),True)]
        cases.extend((str(counts),counts,False) for counts in [
            (0,0,0),(10,0,0),(11,0,0),(100,0,0),
            (1,1,0),(1,10,0),(1,20,0),(1,100,0),
            (1,0,1),(1,0,10),(1,0,20),(1,0,100),(10,20,30)])
        try:
            for label,counts,expected in cases:
                frame=Image.new('RGB',(1920,1080),'white');frame.paste(crop,(10,938))
                if counts is not None:
                    draw=ImageDraw.Draw(frame);draw.rectangle((10,938,910,960),fill='white')
                    records,errors,warnings=counts
                    draw.text((13,940),f'已经处理了{records}条记录、{errors}条错误和{warnings}条警告。',font=font,fill='black')
                with Image.open(self.resource/'image/PSIDE/active_editor_close.png') as icon:
                    frame.paste(icon.convert('RGB'),(1000,200))
                self.controller.frame=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
                keys=[];self.controller.key_hook=lambda key: keys.append(key) or True
                job=self.tasker.post_task('R_BuildExecute',{
                    'R_BuildExecute':{'recognition':'DirectHit','action':'DoNothing','next':['R_BuildFinished'],
                                      'timeout':50,'rate_limit':0,'pre_delay':0,'post_delay':0},
                    'R_BuildFocusEditor':{'recognition':'DirectHit','action':'ClickKey','key':0x20073,
                                         'next':[],'pre_delay':0,'post_delay':0},
                }).wait()
                with self.subTest(case=label):
                    self.assertEqual(job.succeeded,expected)
                    self.assertEqual(keys,[0x20073] if expected else [])
        finally:self.controller.key_hook=None

    def test_service_outcome_reads_the_real_native_terminal_events(self):
        from psauto.evidence import EvidenceSink
        from psauto.objects.models import FieldRequest
        from psauto.objects.service import _business_result
        request=FieldRequest(name='GM_NATIVE',long_name='GM Native',short_name='GM')
        for close in (False,True):
            trace=EvidenceSink(self.tasker)
            try:
                job=self.tasker.post_task('PSIDE_CreateField',{
                    'PSIDE_CreateField':{'enabled':True,'recognition':'DirectHit','action':'DoNothing',
                                         'next':['PSIDE_CreateField_Saved'],'pre_delay':0,'post_delay':0},
                    'PSIDE_CreateField_Saved':{'recognition':'DirectHit','action':'DoNothing',
                        'next':['PSIDE_CreateField_SavedAndClosed'] if close else [],'pre_delay':0,'post_delay':0},
                    'PSIDE_CreateField_SavedAndClosed':{'recognition':'DirectHit','action':'DoNothing',
                                                      'next':[],'pre_delay':0,'post_delay':0},
                }).wait()
                result=_business_result('PSIDE_CreateField',request,job,trace)
                with self.subTest(closed=close):
                    self.assertTrue(result['saved'])
                    self.assertEqual(result['workspace_ready'],close)
                    self.assertEqual(result['success'],close)
            finally:trace.close()

    def test_one_title_recognition_requires_both_the_exact_object_and_step(self):
        from maa.pipeline import JOCR
        from psauto.objects.models import AERequest
        from psauto.objects.ae import build
        for request_name in ['GM_MCP_AE5','GM_MCP_AE','GM_MCP_AE6']:
            _,override=build(AERequest(name=request_name,steps=[{'type':'SQL','code':'SELECT 1'}]*4))
            for step in range(4):
                frame=Image.new('RGB',(1920,1080),'white')
                frame.paste(self.image(f'ae_editor_title_step{step+1:02d}.png'),(0,0))
                pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
                for target in [step,(step+1)%4]:
                    rule=override[f'A{target}_EditorReady']['all_of'][0]
                    result=self.tasker.post_recognition('OCR',JOCR(roi=rule['roi'],expected=[rule['expected']]),pixels).wait().get().nodes[0].recognition
                    with self.subTest(object=request_name,frame_step=step+1,target_step=target+1):
                        self.assertEqual(result.hit,request_name=='GM_MCP_AE5' and step==target)

    def test_editor_object_guard_rejects_an_extra_identifier_prefix(self):
        from maa.pipeline import JOCR
        from psauto.objects.ae import build
        from psauto.objects.models import AERequest
        frame=Image.new('RGB',(1920,1080),'white')
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
        ImageDraw.Draw(frame).text((2,2),
            'Application Designer - HRDEV - GMGM_MCP_AE5 - MAIN.GBL.default.1900-01-01.Step01.SQL',
            font=font,fill='black')
        pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
        for name in ['GMGM_MCP_AE5','GM_MCP_AE5']:
            _,override=build(AERequest(name=name,steps=[{'type':'SQL','code':'SELECT 1'}]))
            rule=override['A0_EditorReady']['all_of'][0]
            result=self.tasker.post_recognition('OCR',JOCR(roi=rule['roi'],expected=[rule['expected']]),pixels).wait().get().nodes[0].recognition
            with self.subTest(name=name):
                self.assertEqual(result.hit,name=='GMGM_MCP_AE5')

    def test_editor_step_guard_rejects_extra_identifier_characters(self):
        from maa.pipeline import JOCR
        from psauto.objects.ae import build
        from psauto.objects.models import AERequest
        _,override=build(AERequest(name='GM_AE_FAST',steps=[{'type':'SQL','code':'SELECT 1'}]))
        rule=override['A0_EditorReady']['all_of'][0]
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
        for token in ['Step01','Step02','Step010','Step01A','XStep01','Step01_','Step01a','xStep01']:
            frame=Image.new('RGB',(1920,1080),'white')
            ImageDraw.Draw(frame).text((2,2),
                'Application Designer - HRDEV - GM_AE_FAST - MAIN.GBL.default.1900-01-01.'+token+'.SQL',
                font=font,fill='black')
            for filename,point in [('sql_editor_icon.png',(600,150)),
                                   ('save_enabled.png',(55,45)),
                                   ('active_editor_close.png',(1000,200))]:
                with Image.open(self.resource/'image/PSIDE'/filename) as icon:
                    frame.paste(icon.convert('RGB'),point)
            pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
            result=self.tasker.post_recognition('OCR',JOCR(roi=rule['roi'],expected=[rule['expected']]),pixels).wait().get().nodes[0].recognition
            with self.subTest(token=token):
                self.assertEqual(result.hit,token=='Step01')
                seen=[]
                self.controller.frame=pixels
                self.controller.key_hook=lambda key: seen.append(key) or True
                try:
                    job=self.tasker.post_task('A0_Paste',{
                        'A0_Paste':{'recognition':'DirectHit','action':'DoNothing','next':['A0_Dirty'],
                                    'timeout':50,'rate_limit':0,'pre_delay':0,'post_delay':0},
                        'A0_Dirty':{**override['A0_Dirty'],'next':[],'post_delay':0},
                    }).wait()
                    self.assertEqual(job.succeeded,token=='Step01')
                    self.assertEqual(seen,[0x20053] if token=='Step01' else [])
                finally:self.controller.key_hook=None

    def test_merged_field_editor_guard_clicks_only_when_both_labels_are_present(self):
        type_label=Image.open(self.resource/'image/PSIDE/field_type_label.png').convert('RGB')
        length_label=Image.open(self.resource/'image/PSIDE/field_length_label.png').convert('RGB')
        try:
            for include_type,include_length in [(True,True),(True,False),(False,True)]:
                frame=Image.new('RGB',(1920,1080),'white')
                if include_type:frame.paste(type_label,(600,250))
                if include_length:frame.paste(length_label,(600,280))
                self.controller.frame=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
                clicks=[]
                self.controller.click_hook=lambda x,y: clicks.append((x,y)) or True
                job=self.tasker.post_task('F_SelectField',{
                    'F_SelectField':{'recognition':'DirectHit','action':'DoNothing','next':['F_TypeFocus'],
                                     'timeout':50,'rate_limit':0,'post_delay':0},
                    'F_TypeFocus':{'post_delay':0},
                    'F_TypeSelect':{'recognition':'DirectHit','action':'DoNothing','next':[]},
                }).wait()
                with self.subTest(type=include_type,length=include_length):
                    self.assertEqual(job.succeeded,include_type and include_length)
                    self.assertEqual(len(clicks),int(include_type and include_length))
                    if clicks:
                        x,y=clicks[0]
                        self.assertTrue(695<=x<600+type_label.width+45)
                        self.assertTrue(258<=y<250+type_label.height-7)
        finally:self.controller.click_hook=None

    def test_native_maa_key_lists_preserve_the_sequential_selection_keys(self):
        try:
            for keys in [[36,13],[36,68,13],[36,0x10023]]:
                seen=[]
                self.controller.key_hook=lambda key: seen.append(key) or True
                job=self.tasker.post_task('F_TypeSelect',{
                    'F_TypeSelect':{'key':keys,'next':[],'post_delay':0}
                }).wait()
                with self.subTest(keys=keys):
                    self.assertTrue(job.succeeded)
                    self.assertEqual(seen,keys)
        finally:self.controller.key_hook=None

    def test_lookup_name_is_exact_after_moving_the_insertion_caret(self):
        from maa.pipeline import JOCR
        for filename, expected in [('lookup_name_caret.png',False),('lookup_name_blurred.png',True)]:
            frame=Image.new('RGB',(1920,1080),'white')
            frame.paste(self.image(filename),(760,420))
            pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
            params=JOCR(roi=(770,420,150,40),expected=['GM[_ ]+MCP[_ ]+REC6'])
            result=self.tasker.post_recognition('OCR',params,pixels).wait().get().nodes[0].recognition
            with self.subTest(frame=filename):self.assertEqual(result.hit,expected)

    def test_save_name_is_exact_without_the_caret_and_build_scope_uses_one_line(self):
        from maa.pipeline import JOCR
        for filename, box, roi, expected in [
            ('save_name_caret.png',(840,520),(840,520,160,30),False),
            ('save_name_blurred.png',(840,520),(840,520,160,30),True),
            ('build_scope_name.png',(780,415),(785,422,165,70),False),
            ('build_scope_name.png',(780,415),(785,420,165,25),True),
        ]:
            frame=Image.new('RGB',(1920,1080),'white')
            frame.paste(self.image(filename),box)
            pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
            params=JOCR(roi=roi,expected=['GM[_ ]+MCP[_ ]+REC6'])
            result=self.tasker.post_recognition('OCR',params,pixels).wait().get().nodes[0].recognition
            with self.subTest(frame=filename,roi=roi):self.assertEqual(result.hit,expected)

    def test_checkbox_click_must_change_state_before_the_next_attribute(self):
        graph = json.loads((self.resource/'pipeline/PSIDE/create_record.json').read_text(encoding='utf-8'))
        pairs = json.loads((self.fixtures/'checkbox_pairs.json').read_text(encoding='utf-8'))
        cases = [(p['node'], p, i) for i, p in enumerate(pairs)]
        # These three inverse paths share the actual Key-uncheck control pixels.
        # They are composed cases, not claims of additional live UI clicks.
        cases.extend((f'R_Attr{label}Uncheck', pairs[9], 9) for label in ['Alternate', 'List', 'Search'])
        try:
            for entry, pair, index in cases:
                x, y, w, h = pair['box']
                captured = self.image(f'checkbox_pair_{index:02d}.png')
                frames = []
                for offset in [0, w]:
                    frame = Image.new('RGB', (1920,1080), 'white')
                    frame.paste(captured.crop((offset,0,offset+w,h)), (x,y))
                    frames.append(np.ascontiguousarray(np.asarray(frame)[:,:,::-1]))
                guard = graph[entry]['next'][0]
                terminal = graph[guard]['next'][0]
                for applied in [True, False]:
                    self.controller.frame = frames[0]
                    clicks = []
                    def click(px, py):
                        clicks.append((px, py))
                        self.assertTrue(x <= px < x+w and y <= py < y+h)
                        if applied:
                            self.controller.frame = frames[1]
                        return True  # An input acknowledgement alone must not pass.
                    self.controller.click_hook = click
                    job = self.tasker.post_task(entry, {
                        entry: {'roi': pair['box'], 'timeout':100, 'rate_limit':0, 'post_delay':0},
                        guard: {'timeout':100, 'rate_limit':0},
                        terminal: {'recognition':'DirectHit', 'action':'DoNothing', 'next':[]},
                    }).wait()
                    with self.subTest(entry=entry, capture=index, changed=applied):
                        self.assertEqual(job.succeeded, applied)
                        self.assertEqual(len(clicks), 1, 'A failed state check must not toggle again')
                        names = [n.name for n in job.get().nodes]
                        self.assertEqual(terminal in names, applied)
        finally:
            self.controller.click_hook = None

    def test_zero_gate_rejects_real_nonzero_blank_and_shifted_zero(self):
        from maa.pipeline import JAnd
        zero = self.image('count_0.png')
        cases = [(str(n),self.image(f'count_{n}.png'),n==0) for n in [0,1,50,17,45,7]]
        cases.append(('blank',self.image('count_blank.png'),False))
        for digits in [1,2]:
            # Compose 10/100 from captured glyph pixels, keeping a shifted zero suffix.
            counter = zero.copy()
            ImageDraw.Draw(counter).rectangle((6,3,170,21),fill=zero.getpixel((110,14)))
            counter.paste(zero.crop((6,3,84,21)),(6+digits*8,3))
            counter.paste(self.image('count_1.png').crop((6,5,13,16)),(6,5))
            if digits==2: counter.paste(zero.crop((6,5,13,16)),(14,5))
            cases.append(('synthetic-'+('10' if digits==1 else '100'),counter,False))
        for kind,prefix in [('field','Field'),('record','Record'),('ae','AE')]:
            graph=json.loads((self.resource/f'pipeline/PSIDE/create_{kind}.json').read_text(encoding='utf-8'))
            params=JAnd(all_of=graph[f'PSIDE_Create{prefix}_query_missing']['all_of'])
            for label,counter,expected in cases:
                frame=Image.new('RGB',(1920,1080),'white')
                frame.paste(self.image('lookup_title.png'),(680,338))
                frame.paste(counter,(690,714))
                pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
                rec=self.tasker.post_recognition('And',params,pixels).wait().get().nodes[0].recognition
                with self.subTest(kind=kind,count=label): self.assertEqual(rec.hit,expected)
            frame=Image.new('RGB',(1920,1080),'white')
            frame.paste(zero,(690,714))
            pixels=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
            self.assertFalse(self.tasker.post_recognition('And',params,pixels).wait().get().nodes[0].recognition.hit,
                             'A zero outside the expected dialog must not pass')

    def test_step_number_guards_reject_a_similar_other_step(self):
        both=Image.new('RGB',(1920,1080),'white')
        both.paste(self.image('steps_01_02.png'),(560,240))
        only1=Image.new('RGB',(1920,1080),'white')
        only1.paste(self.image('step_01_only.png'),(540,210))
        only2=both.copy()
        ImageDraw.Draw(only2).rectangle((550,238,1000,359),fill='white')
        cases=[('both',both,[True,True]),('only01',only1,[True,False]),
               ('only02-synthetic',only2,[False,True]),
               ('none',Image.new('RGB',(1920,1080),'white'),[False,False])]
        for label,frame,expected in cases:
            self.controller.frame=np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
            for index in [0,1]:
                entry=f'A{index}_SelectStep'
                guard=f'A{index}_CheckStepNumber'
                job=self.tasker.post_task(entry,{entry:{'timeout':100},
                    guard:{'action':'DoNothing','next':[],'timeout':100}}).wait()
                with self.subTest(frame=label,step=index+1): self.assertEqual(job.succeeded,expected[index])
