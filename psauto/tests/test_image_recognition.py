"""Native Maa regression checks for similar counters and Step numbers; no browser."""
import json
import os
from pathlib import Path
import unittest

import numpy as np
from PIL import Image, ImageDraw


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
            def connect(self): return True
            def connected(self): return True
            def request_uuid(self): return 'offline-vision-regression'
            def screencap(self): return self.frame.copy()
            def reject_input(self,*args): raise AssertionError('Offline test cannot send input')
            def click(self, x, y):
                if self.click_hook is None:
                    return self.reject_input(x, y)
                return self.click_hook(x, y)
            click_key = key_down = key_up = input_text = reject_input

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
