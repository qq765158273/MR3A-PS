"""Contracts for view SQL, record type routing and Build option selection."""
import json
from pathlib import Path
import unittest

from pydantic import ValidationError

from psauto.objects.models import RecordRequest
from psauto.objects.record import build
from psauto.objects.common import identifier


class RecordKindArgumentsTests(unittest.TestCase):
    def test_full_physical_record_accepts_sixty_columns_and_reaches_each_field_node(self):
        fields = [f'FIELD_{index:02d}' for index in range(61)]
        request = RecordRequest(name='GM_DEPT_TMP', type='Temporary Table', fields=fields, build=True)
        entry, override = build(request)
        source = json.loads((Path(__file__).resolve().parents[2] /
                             'assets/resource/pipeline/PSIDE/create_record.json').read_text(encoding='utf8'))
        graph = {key: {**value, **override.get(key, {})} for key, value in source.items()}
        pending, visited = [entry], set()
        while pending:
            node = pending.pop()
            if node in visited:
                continue
            visited.add(node)
            self.assertIn(node, graph)
            pending.extend(graph[node].get('next', []))
        self.assertEqual(len(request.fields), 61)
        for index in range(61):
            with self.subTest(index=index):
                self.assertIn(f'R_Field{index}_Inserted', visited)
                self.assertEqual(graph[f'R_Field{index}_Name']['expected'], rf'^\s*{identifier(fields[index])}\s*$')
                self.assertEqual(graph[f'R_Field{index}_ConfirmResult']['next'],
                                 [f'R_Field{index}_DuplicateWarning', f'R_Field{index}_Cancel'])
                self.assertEqual(graph[f'R_Field{index}_DuplicateWarning']['next'],
                                 [f'R_Field{index}_DuplicateConfirm'])
                self.assertEqual(graph[f'R_Field{index}_DuplicateConfirm']['next'],
                                 [f'R_Field{index}_Cancel'])
        self.assertIn('R_BuildFinished', visited)
        with self.assertRaises(ValidationError):
            RecordRequest(name='GM_TOO_MANY', fields=[f'FIELD_{i:02d}' for i in range(62)])

    def test_view_sql_and_build_contracts_reject_invalid_requests(self):
        base = {'name': 'GM_KIND_TEST', 'fields': ['SETID']}
        invalid = [
            {'type': 'SQL View'}, {'type': 'Dynamic View'},
            {'type': 'SQL View', 'view_sql': ''}, {'type': 'SQL View', 'view_sql': '\x00'},
            {'type': 'SQL View', 'view_sql': '中' * 22000},
            {'type': 'SQL Table', 'view_sql': 'SELECT SETID FROM PS_DEPT_TBL'},
            {'type': 'Derived/Work', 'build': True},
            {'type': 'Dynamic View', 'view_sql': '/**/', 'build': True},
        ]
        for values in invalid:
            with self.subTest(values={k: str(v)[:50] for k, v in values.items()}), self.assertRaises(ValidationError):
                RecordRequest(**base, **values)

    def test_all_kinds_bind_complete_graphs_and_only_physical_types_build(self):
        source = json.loads((Path(__file__).resolve().parents[2] /
                             'assets/resource/pipeline/PSIDE/create_record.json').read_text(encoding='utf8'))
        sql = 'SELECT SETID FROM PS_DEPT_TBL /* 中文 __PARAM_keep_as_data__ $(not_run) */'
        for kind in ['SQL Table', 'SQL View', 'Dynamic View', 'Derived/Work', 'Temporary Table']:
            physical = kind in {'SQL Table', 'SQL View', 'Temporary Table'}
            for do_build in ([False, True] if physical else [False]):
                request = RecordRequest(name='GM_KIND_TEST', fields=['SETID'], type=kind, build=do_build,
                                        view_sql=sql if kind in {'SQL View', 'Dynamic View'} else None)
                entry, override = build(request)
                graph = {k: {**v, **override.get(k, {})} for k, v in source.items()}
                pending, visited = [entry], set()
                while pending:
                    node = pending.pop()
                    if node in visited:
                        continue
                    visited.add(node)
                    # SQL input is opaque data and may itself contain parameter-looking strings.
                    values = {k: v for k, v in graph[node].items() if k != 'input_text'}
                    self.assertNotIn('__PARAM_', json.dumps(values), (kind, node))
                    pending.extend(graph[node].get('next', []))
                with self.subTest(kind=kind, build=do_build):
                    self.assertEqual('R_ViewPaste' in visited, kind in {'SQL View', 'Dynamic View'})
                    self.assertEqual('R_BuildMenu' in visited, do_build)
                    if request.view_sql is not None:
                        self.assertEqual(override['R_ViewPaste']['input_text'], sql)
                    checks = graph['R_BuildExecute']['all_of']
                    self.assertEqual(checks[2]['template'], 'PSIDE/checkbox_unchecked.png'
                                     if kind == 'SQL View' else 'PSIDE/checkbox_selected.png')
                    self.assertEqual(checks[4]['template'], 'PSIDE/checkbox_selected.png'
                                     if kind == 'SQL View' else 'PSIDE/checkbox_unchecked.png')
