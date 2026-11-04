import json
import importlib.util
from pathlib import Path
import unittest

import jsonschema
from pydantic import ValidationError

from psauto.objects.models import AERequest, AEStep, FieldRequest, RecordRequest
from psauto.objects.service import BUILDERS


class ObjectArgumentsTests(unittest.TestCase):
    def test_invalid_arguments_stop_before_browser_access(self):
        for make in [
            lambda: FieldRequest(name='NOT_GM', long_name='x', short_name='x'),
            lambda: FieldRequest(name='GM_TEST', long_name='x\ny', short_name='x'),
            lambda: RecordRequest(name='GM_TEST', fields=['EMPLID', 'EMPLID']),
            lambda: RecordRequest(name='GM_TEST', fields=['EMPLID', {'name': 'EMPLID', 'key': True}]),
            lambda: RecordRequest(name='GM_TEST', fields=['EMPLID'], build=True),
            lambda: RecordRequest(name='GM_TEST', fields=[{'name': 'EMPLID', 'key': 'yes'}]),
            lambda: RecordRequest(name='GM_TEST', fields=[{'name': 'EFFDT', 'alternate_search_key': True, 'search_key': True}]),
            lambda: AERequest(name='GM_TEST', steps=[{'type': 'Do Select', 'code': 'SELECT 1'}]),
            lambda: AERequest(name='GM_TEST', steps=[{'name': 'Step02', 'type': 'SQL', 'code': 'SELECT 1'}]),
            lambda: AEStep(type='SQL', code='\x00'),
            lambda: AEStep(type='SQL', code='中' * 22000),
        ]:
            with self.subTest(make=make), self.assertRaises(ValidationError):
                make()

    def test_parameterized_graphs_use_native_schema_and_preserve_code_as_data(self):
        project = Path(__file__).resolve().parents[2]
        schema = json.loads((project / 'deps/tools/pipeline.schema.json').read_text(encoding='utf-8'))
        spec = importlib.util.spec_from_file_location('repo_schema', project / 'tools/validate_schema.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        store = {}
        for path in (project / 'deps/tools').glob('*.json'):
            content = module.load_jsonc(path)
            for uri in (path.as_uri(), './' + path.name, '/' + path.name):
                store[uri] = content
        validator = module.create_validator(schema, store)
        code = 'Local string &a;\r\n&a = "中文 $(not_a_command) `literal`";'
        requests = [FieldRequest(name='GM_TEST_F', long_name='GM Field', short_name='GM'),
                    FieldRequest(name='GM_TEST_D', type='Date', long_name='GM Date', short_name='GM'),
                    RecordRequest(name='GM_TEST_R', fields=['GM_TEST_F']),
                    RecordRequest(name='GM_TEST_R', type='SQL Table', tablespace='PSDEFAULT',
                                  fields=[{'name':'EMPLID','key':True,'listbox':True,'search_key':True},
                                          {'name':'EFFDT','alternate_search_key':True,'listbox':True}]),
                    AERequest(name='GM_TEST_A', steps=[{'type': 'SQL', 'code': 'SELECT 1'},
                                                       {'type': 'PeopleCode', 'code': code}])]
        resource_nodes = {}
        for filename in (project / 'assets/resource/pipeline/PSIDE').glob('*.json'):
            resource_nodes.update(json.loads(filename.read_text(encoding='utf-8')))
        for request in requests:
            entry, override = BUILDERS[type(request)](request)
            with self.subTest(entry=entry, type=request.type if hasattr(request, 'type') else 'AE'):
                validator.validate(override)
                merged = {name: {**value, **override.get(name, {})} for name, value in resource_nodes.items()}
                self.assertIn(entry, merged)
                for name, value in override.items():
                    for target in value.get('next', []):
                        self.assertIn(target, merged, (name, target))
                    self.assertLessEqual(set(value), {'expected', 'input_text', 'all_of', 'next', 'enabled', 'custom_action_param', 'key', 'template'}, name)
        _, override = BUILDERS[AERequest](requests[-1])
        self.assertEqual(override['A1_Paste']['input_text'], code)
        for name, value in override.items():
            self.assertNotIn(code, json.dumps(value.get('expected', '')), name)

    def test_record_options_bind_the_existing_mr3a_component(self):
        request=RecordRequest(name='GM_TEST_R',type='SQL Table',tablespace='PSDEFAULT',fields=[
            {'name':'EMPLID','key':True,'listbox':True,'search_key':True},
            'EMPL_RCD',
            {'name':'EFFDT','alternate_search_key':True,'listbox':True}])
        _,override=BUILDERS[RecordRequest](request)
        first=override['R_Attr0_Bind']['custom_action_param']
        last=override['R_Attr2_Bind']['custom_action_param']
        self.assertEqual(first['R_AttrDone']['next'],['R_Attr2_Bind'])
        self.assertEqual(last['R_AttrDone']['next'],['R_TypeTab'])
        self.assertEqual(first['R_AttrKeyLabel']['next'],['R_AttrKeyChecked','R_AttrKeyCheck'])
        self.assertEqual(last['R_AttrKeyLabel']['next'],['R_AttrKeyUnchecked','R_AttrKeyUncheck'])
        self.assertEqual(last['R_AttrAlternateLabel']['next'],['R_AttrAlternateChecked','R_AttrAlternateCheck'])
        self.assertEqual(last['R_AttrSearchLabel']['next'],['R_AttrSearchUnchecked','R_AttrSearchUncheck'])
        self.assertEqual(override['R_SpaceInitial']['key'],ord('P'))
        for payload in (first,last):
            self.assertNotIn('__PARAM_',json.dumps(payload))
            self.assertTrue(all(set(value)<={'expected','next'} for value in payload.values()))

    def test_every_creation_finishes_with_save_and_close_without_readback(self):
        project = Path(__file__).resolve().parents[2]
        resource_nodes = {}
        for filename in (project / 'assets/resource/pipeline/PSIDE').glob('*.json'):
            resource_nodes.update(json.loads(filename.read_text(encoding='utf-8')))
        requests = [FieldRequest(name='GM_TEST_F', long_name='GM Field', short_name='GM'),
                    FieldRequest(name='GM_TEST_D', type='Date', long_name='GM Date', short_name='GM'),
                    RecordRequest(name='GM_TEST_R', fields=['EMPLID']),
                    RecordRequest(name='GM_TEST_R', fields=[f'GM_F{i}' for i in range(20)])]
        for count in range(1, 5):
            for kind in ('SQL', 'PeopleCode'):
                requests.append(AERequest(name='GM_TEST_A', steps=[{'type': kind, 'code': 'payload'}] * count))
        for request in requests:
            entry, override = BUILDERS[type(request)](request)
            graph = {name: {**value, **override.get(name, {})} for name, value in resource_nodes.items()}
            with self.subTest(entry=entry, request=request.model_dump()):
                reached, pending = set(), [entry]
                while pending:
                    name = pending.pop()
                    if name in reached:
                        continue
                    self.assertIn(name, graph)
                    reached.add(name)
                    self.assertNotIn('__PARAM_', json.dumps(graph[name]), name)
                    self.assertNotIn('Verify', name)
                    self.assertNotIn('Reopen', name)
                    pending.extend(graph[name].get('next', []))
                self.assertIn(entry + '_Saved', reached)
                self.assertIn(entry + '_SavedAndClosed', reached)
                tail, pending = [], [entry + '_Saved']
                while pending:
                    name = pending.pop()
                    self.assertNotIn(name, tail, 'Save/close must not loop')
                    tail.append(name)
                    pending.extend(graph[name].get('next', []))
                if isinstance(request, RecordRequest):
                    self.assertEqual([graph[name]['action'] for name in tail],
                                     ['DoNothing', 'ClickKey', 'DoNothing'])
                    self.assertEqual(graph[tail[1]]['key'], 0x20073)
                else:
                    self.assertEqual([graph[name]['action'] for name in tail],
                                     ['DoNothing', 'KeyDown', 'ClickKey', 'KeyUp', 'DoNothing'])
                    self.assertEqual([graph[name].get('key') for name in tail[1:4]], [17, 115, 17])
                self.assertEqual(tail[-1], entry + '_SavedAndClosed')
                self.assertEqual(graph[tail[-1]].get('next', []), [])
                checks = graph[entry + '_Saved']['all_of']
                self.assertTrue(any(c.get('template') == 'PSIDE/save_disabled.png' for c in checks))
                self.assertTrue(any(c.get('template') == 'PSIDE/active_editor_close.png' for c in checks))
