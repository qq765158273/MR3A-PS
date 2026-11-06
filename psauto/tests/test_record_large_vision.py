"""Native image regressions for auto insertion and O/0 in field names."""
import os
import unittest
import numpy as np
from PIL import Image
from psauto.objects.models import RecordRequest
from psauto.objects.record import build
import test_image_recognition as native_vision


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_OCR'), 'Native vision integration not enabled')
class LargeRecordVisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native_vision.ImageRecognitionTests.setUpClass.__func__(cls)

    def test_auto_insert_state_requires_selected_result_and_dialog(self):
        for fixture, erase_dialog, expected in [
            ('record_unique_insert_selected.png', False, True),
            ('record_multiple_insert_unselected.png', False, False),
            ('record_unique_insert_selected.png', True, False),
        ]:
            with Image.open(self.fixtures / fixture) as im:
                frame = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()
            if erase_dialog:
                frame[335:380, 680:1240] = 255
            self.controller.frame = frame
            job = self.tasker.post_task('R_Field0_AutoInserted', {
                'R_Field0_AutoInserted': {'action': 'DoNothing', 'next': [],
                                         'timeout': 100, 'rate_limit': 0, 'pre_delay': 0, 'post_delay': 0}
            }).wait()
            with self.subTest(fixture=fixture, erase_dialog=erase_dialog):
                self.assertEqual(job.succeeded, expected)

    def test_eeo4_input_uses_exact_name_and_rejects_wrong_requested_field(self):
        with Image.open(self.fixtures / 'record_eeo4_input.png') as im:
            self.controller.frame = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()
        for field, expected in [('EEO4_FUNCTION', True), ('EEO4_FUNCTION_X', False), ('X_EEO4_FUNCTION', False)]:
            _, ov = build(RecordRequest(name='GM_VISION', fields=[field]))
            ov.setdefault('R_Field0_Name', {}).update(next=[], timeout=100, rate_limit=0)
            job = self.tasker.post_task('R_Field0_Name', ov).wait()
            with self.subTest(field=field):
                self.assertEqual(job.succeeded, expected)

    def test_row_count_is_read_from_one_cell_and_clicks_only_that_row(self):
        clicks = []
        self.controller.click_hook = lambda x, y: clicks.append((x, y)) or True
        try:
            for fixture, actual, node, top in [
                ('record_row25.png', 25, 'R_Field24_Inserted', 540),
                ('record_row61.png', 61, 'R_Field60_Inserted', 863),
            ]:
                with Image.open(self.fixtures / fixture) as im:
                    self.controller.frame = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()
                for number in [actual, actual - 1, actual // 10, actual % 10, actual + 100]:
                    clicks.clear()
                    job = self.tasker.post_task(node, {node: {
                        'expected': rf'^\s*{number}\s*$', 'next': [],
                        'timeout': 100, 'rate_limit': 0, 'post_delay': 0}
                    }).wait()
                    with self.subTest(fixture=fixture, number=number):
                        self.assertEqual(job.succeeded, number == actual)
                        self.assertEqual(len(clicks), int(number == actual))
                        if number == actual:
                            self.assertTrue(463 <= clicks[0][0] < 485 and top <= clicks[0][1] < top + 15)
        finally:
            self.controller.click_hook = None

    def test_all_visible_counter_cells_in_real_eleven_and_twentyfive_row_frames(self):
        from maa.pipeline import JOCR
        for fixture, count in [('record_row11.png', 11), ('record_row25.png', 25)]:
            with Image.open(self.fixtures / fixture) as im:
                frame = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()
            for index in range(count):
                result = self.tasker.post_recognition('OCR', JOCR(
                    roi=[463, 132 + 17 * index, 22, 15], only_rec=True,
                    expected=[rf'^\s*{index + 1}\s*$']), frame).wait().get().nodes[0].recognition
                with self.subTest(fixture=fixture, row=index + 1):
                    self.assertTrue(result.hit)
