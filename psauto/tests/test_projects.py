"""Project manifest validation and native image guards, without browser input."""
import json
import os
from pathlib import Path
import unittest

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pydantic import ValidationError

from psauto.objects.models import ProjectRequest
from psauto.objects.project import build
import test_image_recognition as native_vision


class ProjectArgumentsTests(unittest.TestCase):
    def test_invalid_manifests_are_rejected_before_automation(self):
        good = {'name': 'GM_PROJECT', 'definitions': [{'type': 'AE', 'name': 'GM_DEPT_XL4'}]}
        for change in [
            {'name': 'OTHER'}, {'name': 'GM_' + 'X' * 16}, {'definitions': []},
            {'definitions': [{'type': 'SQL', 'name': 'GM_SQL'}]},
            {'definitions': [{'type': 'Record', 'name': 'GM%'}]},
            {'definitions': [{'type': 'AE', 'name': 'A' * 13}]},
            {'definitions': good['definitions'] * 2},
            {'definitions': [{'type': 'Field', 'name': 'X' + str(i)} for i in range(21)]},
        ]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                ProjectRequest(**{**good, **change})

    def test_only_requested_slots_are_reachable_and_bound(self):
        source = json.loads((Path(__file__).resolve().parents[2] /
                             'assets/resource/pipeline/PSIDE/create_project.json').read_text(encoding='utf8'))
        request = ProjectRequest(name='GM_PROJECT', definitions=[
            {'type': 'AE', 'name': 'GM_DEPT_XL4'}, {'type': 'Record', 'name': 'GM_DEPT_AET'},
            {'type': 'Field', 'name': 'GM_MCP_EMPLID'}])
        entry, override = build(request)
        graph = {name: {**value, **override.get(name, {})} for name, value in source.items()}
        visited, pending = set(), [entry]
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)
            self.assertNotIn('__PARAM_', json.dumps(graph[name]), name)
            self.assertEqual(graph[name]['on_error'], [], name)
            pending.extend(graph[name].get('next', []))
        self.assertIn('P2_Inserted', visited)
        self.assertNotIn('P3_NewSearch', visited)
        self.assertEqual(graph['P2_Inserted']['next'], ['P_CloseDialog'])


@unittest.skipUnless(os.environ.get('PSAUTO_TEST_OCR'), 'Native vision integration not enabled')
class ProjectRecognitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native_vision.ImageRecognitionTests.setUpClass.__func__(cls)

    def frame(self, name):
        with Image.open(self.fixtures / name) as image:
            return np.asarray(image.convert('RGB'))[:, :, ::-1].copy()

    def task(self, node, *, program='GM_DEPT_P_CAL', kind='AE', definition='GM_DEPT_XL4'):
        _, override = build(ProjectRequest(name=program, definitions=[{'type': kind, 'name': definition}]))
        override['PSIDE_CreateProject'] = {'enabled': True, 'recognition': 'DirectHit', 'action': 'DoNothing',
                                           'next': [node], 'pre_delay': 0, 'post_delay': 0, 'timeout': 100, 'rate_limit': 0}
        override.setdefault(node, {}).update(next=[], pre_delay=0, post_delay=0, timeout=100, rate_limit=0)
        return self.tasker.post_task('PSIDE_CreateProject', override).wait()

    def test_insert_requires_exact_selected_object_and_related_categories(self):
        try:
            for kind, name, fixture in [('AE', 'GM_DEPT_XL4', 'project_ae_selected.png'),
                                        ('Record', 'GM_DEPT_AET', 'project_record_top_selected.png'),
                                        ('Field', 'GM_MCP_EMPLID', 'project_field_selected.png')]:
                for change, passed in [('valid', True), ('prefix', False), ('related_unselected', False),
                                       ('result_unselected', False), ('count_blank', False),
                                       ('count_two', False), ('count_eleven', False)]:
                    frame = self.frame(fixture)
                    if change == 'related_unselected':
                        frame[416:494, 976:1129] = 255
                    if change == 'result_unselected':
                        frame[565:581, 990:1181] = 255
                    if change.startswith('count_'):
                        frame[718:733, 695:707] = 255
                        if change != 'count_blank':
                            image = Image.fromarray(frame[:, :, ::-1])
                            ImageDraw.Draw(image).text((695, 716), '2' if change == 'count_two' else '11',
                                                      fill='black', font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 11))
                            frame = np.asarray(image)[:, :, ::-1].copy()
                    self.controller.frame = frame
                    clicks = []
                    self.controller.click_hook = lambda x, y: clicks.append((x, y)) or True
                    job = self.task('P0_Insert', kind=kind, definition=name[:-1] if change == 'prefix' else name)
                    with self.subTest(kind=kind, change=change):
                        self.assertEqual(job.succeeded, passed)
                        self.assertEqual(len(clicks), int(passed))
        finally:
            self.controller.click_hook = None

    def test_saved_project_rejects_prefix_and_wrong_name_before_reset(self):
        try:
            for name, passed in [('GM_DEPT_P_CAL', True), ('GM_DEPT_P', False), ('GM_OTHER', False)]:
                self.controller.frame = self.frame('project_saved.png')
                keys = []
                self.controller.key_hook = lambda key: keys.append(key) or True
                job = self.task('P_CloseNew', program=name)
                with self.subTest(name=name):
                    self.assertEqual(job.succeeded, passed)
                    self.assertEqual(keys, [0x2004e] if passed else [])
        finally:
            self.controller.key_hook = None

    def test_record_scroll_checks_hidden_top_categories_before_insert(self):
        try:
            for missing_top, passed in [(False, True), (True, False)]:
                self.controller.frame = self.frame('project_record_selected.png')
                target = self.frame('project_record_top_selected.png')
                if missing_top:
                    target[416:441, 976:1111] = 255
                clicks = []
                def click(x, y):
                    clicks.append((x, y))
                    if len(clicks) == 2:
                        self.controller.frame = target.copy()
                    return True
                self.controller.click_hook = click
                _, override = build(ProjectRequest(name='GM_TEST', definitions=[{'type': 'Record', 'name': 'GM_DEPT_AET'}]))
                override['PSIDE_CreateProject'] = {'enabled': True, 'recognition': 'DirectHit', 'action': 'DoNothing',
                    'next': ['P0_RelatedScrollTop'], 'timeout': 100, 'rate_limit': 0, 'pre_delay': 0, 'post_delay': 0}
                for node in ['P0_RelatedScrollTop', 'P0_RelatedScrollAgain', 'P0_Insert']:
                    override.setdefault(node, {}).update(timeout=100, rate_limit=0, pre_delay=0, post_delay=0)
                override['P0_Insert']['next'] = []
                job = self.tasker.post_task('PSIDE_CreateProject', override).wait()
                with self.subTest(missing_top=missing_top):
                    self.assertEqual(job.succeeded, passed)
                    self.assertEqual(len(clicks), 3 if passed else 2)
        finally:
            self.controller.click_hook = None

    def test_empty_workspace_rejects_unsaved_members_or_modal_dialog(self):
        source = json.loads((self.resource / 'pipeline/PSIDE/create_project.json').read_text(encoding='utf8'))
        for fixture, passed in [('project_empty.png', True), ('project_ae_selected.png', False),
                                ('project_ae_inserted.png', False), ('project_saved.png', False)]:
            self.controller.frame = self.frame(fixture)
            if fixture == 'project_ae_inserted.png':
                self.controller.frame[80:880, 435:1505] = 173  # Remove modal; leave unsaved tree members.
            node = {**source['PSIDE_CreateProject'], 'enabled': True, 'next': [], 'timeout': 100, 'rate_limit': 0}
            job = self.tasker.post_task('PSIDE_CreateProject', {'PSIDE_CreateProject': node}).wait()
            with self.subTest(fixture=fixture):
                self.assertEqual(job.succeeded, passed)
