"""Native Maa tests for AET/default and restart guards; no browser input."""
import os
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

from psauto.objects.ae import build
from psauto.objects.models import AERequest
import test_image_recognition as native_vision


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_OCR'), 'Native vision integration not enabled')
class AEPropertyRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native_vision.ImageRecognitionTests.setUpClass.__func__(cls)

    def frame(self,name):
        with Image.open(self.fixtures/name) as image:
            return np.asarray(image.convert('RGB'))[:,:,::-1].copy()

    def task(self,node,patches=None,*,state='GM_DEPT_AET',restart=True,program='GM_DEPT_XLSX'):
        _,override=build(AERequest(name=program,steps=[{'type':'PeopleCode','code':'payload'}],
                                  state_record=state,disable_restart=restart))
        override['PSIDE_CreateAE']={'enabled':True,'recognition':'DirectHit','action':'DoNothing',
                                   'next':[node],'pre_delay':0,'post_delay':0,'timeout':100,'rate_limit':0}
        for key,value in (patches or {}).items():override.setdefault(key,{}).update(value)
        return self.tasker.post_task('PSIDE_CreateAE',override).wait()

    def test_state_binding_requires_exact_default_record(self):
        self.controller.frame=self.frame('ae_properties_state_bound.png')
        for name,passed in [('GM_DEPT_AET',True),('GM_DEPT_AET_X',False),('GM_DEPT_AE',False)]:
            with self.subTest(record=name):
                job=self.task('AEProp_StateBound',{'AEProp_StateBound':{'next':[]}},state=name)
                self.assertEqual(job.succeeded,passed)

    def test_qualify_cannot_modify_an_occupied_state_list(self):
        try:
            for filename,passed in [('ae_properties_state_empty.png',True),('ae_properties_state_bound.png',False)]:
                self.controller.frame=self.frame(filename)
                clicks=[];self.controller.click_hook=lambda x,y: clicks.append((x,y)) or True
                job=self.task('AEProp_Qualify',{'AEProp_Qualify':{'next':[]}})
                self.assertEqual(job.succeeded,passed)
                self.assertEqual(len(clicks),int(passed))
        finally:self.controller.click_hook=None

    def test_state_name_must_share_the_first_default_rows_checkbox(self):
        frame=self.frame('ae_properties_state_bound.png')
        frame[432:450,985:1125]=frame[414:432,985:1125].copy()
        frame[413:432,985:1125]=255
        self.controller.frame=frame
        job=self.task('AEProp_StateBound',{'AEProp_StateBound':{'next':[]}})
        self.assertFalse(job.succeeded,'A matching second row is not the checked default first row')

    def test_full_state_candidates_reject_nonempty_lower_rows_without_any_input(self):
        try:
            for layout,passed,expected_clicks in [('empty',True,1),('bound',True,0),('lower_row',False,0)]:
                frame=self.frame('ae_properties_state_empty.png' if layout=='empty' else 'ae_properties_state_bound.png')
                if layout=='lower_row':
                    frame[432:450,985:1125]=frame[414:432,985:1125].copy()
                    frame[413:432,985:1125]=255
                self.controller.frame=frame
                clicks=[];self.controller.click_hook=lambda x,y: clicks.append((x,y)) or True
                job=self.task('AEProp_StateTab',{
                    'AEProp_StateTab':{'recognition':'DirectHit','action':'DoNothing','next':['AEProp_StateBound','AEProp_Qualify'],
                                       'pre_delay':0,'post_delay':0,'timeout':100,'rate_limit':0},
                    'AEProp_StateBound':{'next':[]},'AEProp_Qualify':{'next':[]}})
                with self.subTest(layout=layout):
                    self.assertEqual(job.succeeded,passed)
                    self.assertEqual(len(clicks),expected_clicks)
        finally:self.controller.click_hook=None

    def test_property_identity_rejects_prefix_on_real_active_title_before_click_or_save(self):
        try:
            for node,fixture in [('AEProp_OpenFileMenu','ae_properties_before_open.png'),
                                 ('AEProp_Save','ae_properties_before_save.png'),
                                 ('AEProp_Saved','ae_properties_before_open.png')]:
                for name,passed in [('GM_DEPT_XL3',True),('GM_DEPT_XL',False),('GM_DEPT',False),('GM_DEPT_XL4',False)]:
                    with self.subTest(node=node,requested=name):
                        self.controller.frame=self.frame(fixture)
                        clicks=[];keys=[]
                        self.controller.click_hook=lambda x,y: clicks.append((x,y)) or True
                        self.controller.key_hook=lambda key: keys.append(key) or True
                        job=self.task(node,{node:{'next':[],'post_delay':0}},program=name)
                        self.assertEqual(job.succeeded,passed)
                        self.assertEqual(len(clicks),int(passed and node=='AEProp_OpenFileMenu'))
                        self.assertEqual(len(keys),int(passed and node=='AEProp_Save'))
        finally:self.controller.click_hook=self.controller.key_hook=None

    def test_restart_toggles_only_once_then_verifies_requested_state(self):
        try:
            for initially_on,wanted,apply_change,passed in [(False,True,True,True),(True,False,True,True),
                                                          (True,True,False,True),(False,False,False,True),
                                                          (False,True,False,False)]:
                with self.subTest(initial=initially_on,wanted=wanted,click_effect=apply_change):
                    self.controller.frame=self.frame('ae_properties_restart_on.png' if initially_on else 'ae_properties_restart_off.png')
                    clicks=[]
                    def click(x,y):
                        clicks.append((x,y))
                        if apply_change:
                            self.controller.frame=self.frame('ae_properties_restart_on.png' if wanted else 'ae_properties_restart_off.png')
                        return True
                    self.controller.click_hook=click
                    job=self.task('AEProp_AdvancedTab',{
                        'AEProp_AdvancedTab':{'recognition':'DirectHit','action':'DoNothing','next':['AEProp_RestartVerified','AEProp_ToggleRestart'],
                                              'pre_delay':0,'post_delay':0,'timeout':100,'rate_limit':0},
                        'AEProp_ToggleRestart':{'post_delay':0,'timeout':100,'rate_limit':0},
                        'AEProp_RestartVerified':{'next':[],'timeout':100,'rate_limit':0}},restart=wanted)
                    self.assertEqual(job.succeeded,passed)
                    self.assertEqual(len(clicks),int(initially_on!=wanted))
        finally:self.controller.click_hook=None
