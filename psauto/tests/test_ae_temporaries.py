"""Temporary-table parameter contracts and native selected-row recognition."""
import json
import os
from pathlib import Path
import unittest

import numpy as np
from PIL import Image
from pydantic import ValidationError

from psauto.objects.ae import build
from psauto.objects.models import AERequest
import test_image_recognition as native_vision


class AETemporaryArgumentsTests(unittest.TestCase):
    def test_temp_names_count_and_uniqueness_are_validated(self):
        base = {'name': 'GM_TEMP_TEST', 'steps': [{'type': 'SQL', 'code': 'SELECT 1 FROM DUAL'}]}
        self.assertEqual(AERequest(**base, temporary_records=['GM_A']).temporary_table_instances, 3)
        for names in [[], ['bad-name'], ['GM_A', 'GM_A'], ['GM_' + str(i) for i in range(11)]]:
            with self.subTest(names=names), self.assertRaises(ValidationError):
                AERequest(**base, temporary_records=names)

    def test_state_temp_restart_combinations_bind_only_requested_paths(self):
        source = json.loads((Path(__file__).resolve().parents[2] /
                             'assets/resource/pipeline/PSIDE/create_ae.json').read_text(encoding='utf8'))
        for state in [None, 'GM_DEPT_AET']:
            for temps in [None, ['GM_KIND_TMP'], ['GM_Z', 'GM_A']]:
                for restart in [None, False, True]:
                    request = AERequest(name='GM_TEMP_TEST', steps=[{'type': 'SQL', 'code': 'SELECT 1 FROM DUAL'}],
                                        state_record=state, temporary_records=temps, disable_restart=restart)
                    entry, ov = build(request)
                    graph = {k: {**v, **ov.get(k, {})} for k, v in source.items()}
                    todo, seen = [entry], set()
                    while todo:
                        name = todo.pop()
                        if name in seen:
                            continue
                        seen.add(name)
                        self.assertNotIn('__PARAM_', json.dumps(graph[name]), name)
                        todo.extend(graph[name].get('next', []))
                    with self.subTest(state=state, temps=temps, restart=restart):
                        self.assertEqual('AEProp_TempTab' in seen, temps is not None)
                        self.assertEqual('AEProp_InstanceCountFocus' in seen, temps is not None)
                        self.assertEqual('AEProp_StateTab' in seen, state is not None)
                        self.assertEqual('AEProp_AdvancedTab' in seen, restart is not None)
                        if temps:
                            self.assertEqual(ov['AEProp_InstanceCountPaste']['input_text'], '3')
                            self.assertNotIn(f'AEProp_Temp{len(temps)}_Qualify', seen)
                            self.assertEqual(ov['AEProp_Temp0_Paste']['input_text'], sorted(temps)[0])
                            self.assertIn('AEProp_TempProjectPrompt', seen)


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_OCR'), 'Native vision integration not enabled')
class AETemporaryRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native_vision.ImageRecognitionTests.setUpClass.__func__(cls)

    def test_selected_temp_must_be_the_requested_first_row(self):
        with Image.open(self.fixtures / 'ae_temp_bound_one.png') as im:
            frame = np.asarray(im.convert('RGB'))[:, :, ::-1].copy()
        for record, move, passed in [('GM_KIND_TMP', False, True), ('GM_KIND_TM', False, False),
                                    ('GM_KIND_TMP', True, False)]:
            pixels = frame.copy()
            if move:
                pixels[435:455, 968:1123] = pixels[412:432, 968:1123].copy()
                pixels[412:432, 968:1123] = 255
            self.controller.frame = pixels
            _, ov = build(AERequest(name='GM_TEMP_TEST', steps=[{'type': 'SQL', 'code': 'SELECT 1 FROM DUAL'}],
                                   temporary_records=[record]))
            ov['PSIDE_CreateAE'] = {'enabled': True, 'recognition': 'DirectHit', 'action': 'DoNothing',
                                   'next': ['AEProp_Temp0_Bound'], 'timeout': 100, 'rate_limit': 0,
                                   'pre_delay': 0, 'post_delay': 0}
            ov.setdefault('AEProp_Temp0_Bound', {}).update(next=[], timeout=100, rate_limit=0)
            job = self.tasker.post_task('PSIDE_CreateAE', ov).wait()
            with self.subTest(record=record, move=move):
                self.assertEqual(job.succeeded, passed)
