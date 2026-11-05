"""Offline native regressions for new type, identity and empty-list guards."""
import json
import os
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

from psauto.objects.ae import build as ae_build
from psauto.objects.models import AERequest, RecordRequest
from psauto.objects.record import build as record_build
import test_image_recognition as native_vision


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_OCR'), 'Native vision integration not enabled')
class CommonKindsVisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native_vision.ImageRecognitionTests.setUpClass.__func__(cls)

    def frame(self, file):
        with Image.open(self.fixtures / file) as im:
            return np.asarray(im.convert('RGB'))[:, :, ::-1].copy()

    def isolated(self, entry, node, override):
        override[entry] = {'enabled': True, 'recognition': 'DirectHit', 'action': 'DoNothing',
                           'next': [node], 'timeout': 100, 'rate_limit': 0, 'pre_delay': 0, 'post_delay': 0}
        override.setdefault(node, {}).update(next=[], timeout=100, rate_limit=0, pre_delay=0, post_delay=0)
        return self.tasker.post_task(entry, override).wait()

    def test_tight_sql_title_distinguishes_zero_from_letter_o_and_prefix(self):
        try:
            self.controller.frame = self.frame('view_sql_title_zero.png')
            for name, passed in [('GM_C_VW01', True), ('GM_C_VWO1', False), ('GM_C_VW', False)]:
                _, ov = record_build(RecordRequest(name=name, fields=['SETID'], type='SQL View', view_sql='SELECT SETID FROM PS_DEPT_TBL'))
                # Focused code clicks require the native icon anchor established just before them.
                ov['PSIDE_CreateRecord'] = {'enabled': True, 'recognition': 'DirectHit', 'action': 'DoNothing',
                    'next': ['R_ViewIcon'], 'timeout': 100, 'rate_limit': 0, 'pre_delay': 0, 'post_delay': 0}
                ov.setdefault('R_ViewIcon', {}).update(timeout=100, rate_limit=0)
                ov.setdefault('R_ViewEditorReady', {}).update(next=[], timeout=100, rate_limit=0, post_delay=0)
                clicks = []
                self.controller.click_hook = lambda x, y: clicks.append((x, y)) or True
                job = self.tasker.post_task('PSIDE_CreateRecord', ov).wait()
                with self.subTest(name=name):
                    self.assertEqual(job.succeeded, passed)
                    self.assertEqual(len(clicks), int(passed))
        finally:
            self.controller.click_hook = None

    def test_each_new_record_kind_rejects_a_different_selected_radio(self):
        cases = [('SQL View', 'record_kind_view.png', 'R_ViewTypeSelected'),
                 ('Dynamic View', 'record_kind_dynamic.png', 'R_DynamicTypeSelected'),
                 ('Temporary Table', 'record_kind_temp.png', 'R_TemporaryTypeSelected')]
        for actual, image, _ in cases:
            self.controller.frame = self.frame(image)
            for wanted, _, target in cases:
                _, ov = record_build(RecordRequest(name='GM_NATIVE', fields=['SETID'], type=wanted,
                    view_sql='SELECT SETID FROM PS_DEPT_TBL' if wanted != 'Temporary Table' else None))
                ov['PSIDE_CreateRecord'] = {'enabled': True, 'recognition': 'DirectHit', 'action': 'DoNothing',
                    'next': ['R_RecordTypeGroup'], 'timeout': 100, 'rate_limit': 0, 'pre_delay': 0, 'post_delay': 0}
                ov['R_RecordTypeGroup'] = {'roi': [430,130,1100,500], 'roi_offset': [0,0,0,0], 'next': [target],
                                           'timeout': 100, 'rate_limit': 0, 'post_delay': 0}
                ov.setdefault(target, {}).update(next=[], timeout=100, rate_limit=0)
                job = self.tasker.post_task('PSIDE_CreateRecord', ov).wait()
                with self.subTest(actual=actual, wanted=wanted):
                    self.assertEqual(job.succeeded, actual == wanted)

    def test_legacy_work_record_still_passes_the_saved_identity_guard(self):
        self.controller.frame = self.frame('record_saved_work.png')
        _, ov = record_build(RecordRequest(name='GM_DEPT_AET', fields=['PROCESS_INSTANCE', 'FILE_NAME']))
        self.assertTrue(self.isolated('PSIDE_CreateRecord', 'PSIDE_CreateRecord_Saved', ov).succeeded)

    def test_ae_close_clicks_only_the_saved_exact_parent_close_button(self):
        try:
            self.controller.frame = self.frame('ae_saved_temp_cal.png')
            for name, passed in [('GM_TEMP_CAL', True), ('GM_TEMP_CA', False)]:
                _, ov = ae_build(AERequest(name=name, steps=[{'type':'SQL','code':'SELECT 1 FROM DUAL'}]))
                clicks = []
                self.controller.click_hook = lambda x, y: clicks.append((x, y)) or True
                job = self.isolated('PSIDE_CreateAE', 'A_CloseSaved', ov)
                with self.subTest(name=name):
                    self.assertEqual(job.succeeded, passed)
                    self.assertEqual(len(clicks), int(passed))
                    if passed:
                        self.assertGreater(clicks[0][0], 1400)
        finally:
            self.controller.click_hook = None

    def test_temp_list_must_be_completely_empty_before_adding(self):
        _, ov = ae_build(AERequest(name='GM_NATIVE_AE', steps=[{'type':'SQL','code':'SELECT 1 FROM DUAL'}],
                                  temporary_records=['GM_KIND_TMP']))
        for image, passed in [('ae_temps_empty.png', True), ('ae_temp_bound_one.png', False)]:
            self.controller.frame = self.frame(image)
            job = self.isolated('PSIDE_CreateAE', 'AEProp_TempsEmpty', dict(ov))
            with self.subTest(image=image):
                self.assertEqual(job.succeeded, passed)
