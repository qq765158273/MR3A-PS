import json
import importlib.util
from pathlib import Path
import unittest

import jsonschema
from pydantic import ValidationError

from psauto.objects.models import AERequest, AEStep, FieldRequest, RecordRequest
from psauto.objects.service import BUILDERS


class ObjectArgumentsTests(unittest.TestCase):
    def test_merged_editor_save_keeps_identity_icon_focus_and_save_feedback_guards(self):
        project=Path(__file__).resolve().parents[2]
        graph=json.loads((project/'assets/resource/pipeline/PSIDE/create_ae.json').read_text(encoding='utf-8'))
        for i in range(4):
            node=graph[f'A{i}_Dirty']
            self.assertEqual(node['action'],'ClickKey')
            self.assertEqual(node['key'],0x20053)
            self.assertEqual(node['next'],[f'A{i}_PSIDE_CodeEditorSaved'])
            self.assertEqual(node['timeout'],30000)
            self.assertEqual(sum(c['recognition']=='OCR' for c in node['all_of']),1)
            templates={c.get('template') for c in node['all_of'] if c['recognition']=='TemplateMatch'}
            self.assertTrue({'PSIDE/save_enabled.png','PSIDE/active_editor_close.png'}.issubset(templates))
            self.assertIn(f'__PARAM_step_{i}_editor_template__',templates)
            self.assertEqual(graph[f'A{i}_PSIDE_CodeEditorSaved']['all_of'][0]['template'],'PSIDE/save_disabled.png')

    def test_field_and_ae_blur_name_before_exact_recognition(self):
        project=Path(__file__).resolve().parents[2]
        for kind,prefix,save in [('field','PSIDE_CreateField','F_Save'),
                                 ('ae','PSIDE_CreateAE','A0_StructureSave')]:
            graph=json.loads((project/f'assets/resource/pipeline/PSIDE/create_{kind}.json').read_text(encoding='utf-8'))
            for source,blur,check in [(prefix+'_query_name_clear_input',prefix+'_query_name_blur',prefix+'_query_name_check'),
                                      (save+'_as',save+'_name_blur',save+'_name')]:
                with self.subTest(kind=kind,source=source):
                    self.assertEqual(graph[source]['next'],[blur])
                    self.assertEqual(graph[blur]['key'],9)
                    self.assertEqual(graph[blur]['next'],[check])
                    self.assertEqual(graph[check]['expected'],'__PARAM_name_regex__')

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
            lambda: AERequest(name='GM_TEST',steps=[{'type':'SQL','code':'x'}],state_record='invalid'),
            lambda: AERequest(name='GM_TEST',steps=[{'type':'SQL','code':'x'}],disable_restart='yes'),
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

    def test_optional_ae_properties_run_before_code_and_bind_only_requested_states(self):
        source=json.loads((Path(__file__).resolve().parents[2]/'assets/resource/pipeline/PSIDE/create_ae.json').read_text(encoding='utf-8'))
        for state, restart in [(None,None),('GM_DEPT_AET',None),(None,True),(None,False),('GM_DEPT_AET',True)]:
            with self.subTest(state=state,restart=restart):
                request=AERequest(name='GM_TEST_A',steps=[{'type':'PeopleCode','code':'payload'}],
                                  state_record=state,disable_restart=restart)
                _,override=BUILDERS[AERequest](request)
                graph={key:{**value,**override.get(key,{})} for key,value in source.items()}
                if state is None and restart is None:
                    self.assertEqual(graph['A0_StructureSave_named']['next'],['A0_TypeSaved'])
                    continue
                self.assertEqual(graph['A0_StructureSave_named']['next'],['AEProp_OpenFileMenu'])
                self.assertEqual(graph['AEProp_Ready']['next'],['AEProp_StateTab' if state else 'AEProp_AdvancedTab'])
                if state:
                    self.assertEqual(override['AEProp_PasteState']['input_text'],state)
                    self.assertEqual(graph['AEProp_StateBound']['next'],['AEProp_AdvancedTab' if restart is not None else 'AEProp_OK'])
                if restart is not None:
                    wanted=override['AEProp_RestartVerified']['template']
                    self.assertIn('PSIDE/checkbox_selected.png' if restart else 'PSIDE/checkbox_unchecked.png',wanted)

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
                self.assertEqual([graph[name]['action'] for name in tail],
                                 ['DoNothing', 'ClickKey', 'DoNothing'])
                self.assertEqual(graph[tail[1]]['key'], 0x20073)
                self.assertEqual(tail[-1], entry + '_SavedAndClosed')
                self.assertEqual(graph[tail[-1]].get('next', []), [])
                checks = graph[entry + '_Saved']['all_of']
                self.assertTrue(any(c.get('template') == 'PSIDE/save_disabled.png' for c in checks))
                self.assertTrue(any(c.get('template') == 'PSIDE/active_editor_close.png' for c in checks))
