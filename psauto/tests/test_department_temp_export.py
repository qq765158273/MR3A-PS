"""Contract checks for the department Temporary Table export manifest."""
import json
from pathlib import Path
import re
import unittest

from psauto.objects.models import AERequest, RecordRequest


class DepartmentTemporaryExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1] / 'demos' / 'dept_export'
        cls.columns = json.loads((cls.root / 'columns.json').read_text(encoding='utf-8'))
        cls.record = json.loads((cls.root / 'record_request.json').read_text(encoding='utf-8'))
        cls.ae = json.loads((cls.root / 'ae_request.json').read_text(encoding='utf-8'))

    def test_record_contains_process_instance_and_all_physical_columns(self):
        self.assertEqual(len(self.columns), 60)
        request = RecordRequest(**self.record)
        names = [field if isinstance(field, str) else field.name for field in request.fields]
        self.assertEqual(names, ['PROCESS_INSTANCE', *self.columns])
        self.assertEqual([name for name in names if name in {'PROCESS_INSTANCE', 'SETID', 'DEPTID', 'EFFDT'}],
                         ['PROCESS_INSTANCE', 'SETID', 'DEPTID', 'EFFDT'])
        self.assertTrue(request.build)
        self.assertEqual(request.type, 'Temporary Table')

    def test_ae_has_insert_then_instance_scoped_export(self):
        request = AERequest(**self.ae)
        self.assertEqual(request.name, 'GM_DEPT_XL5')
        self.assertEqual(request.temporary_records, ['GM_DEPT_TMP'])
        self.assertTrue(request.disable_restart)
        self.assertEqual([step.type for step in request.steps], ['SQL', 'PeopleCode'])
        insert = request.steps[0].code
        self.assertIn('INSERT INTO %Table(GM_DEPT_TMP)', insert)
        self.assertIn('SELECT %ProcessInstance,', insert)
        self.assertIn('FROM PS_DEPT_TBL', insert)
        peoplecode = request.steps[1].code
        self.assertIn('FROM %Table(GM_DEPT_TMP)', peoplecode)
        self.assertIn('WHERE PROCESS_INSTANCE = :1', peoplecode)
        self.assertEqual(int(re.search(r'If &row\.Len <> (\d+) Then', peoplecode).group(1)), 60)
        self.assertIn('&program | " COMPLETE; source=GM_DEPT_TMP', peoplecode)

    def test_peoplecode_sql_literals_fit_compiler_limit_and_preserve_all_columns(self):
        code = self.ae['steps'][1]['code']
        literals = re.findall(r'"([^"\n]*)"', code)
        self.assertLessEqual(max(map(len, literals)), 1000)
        assignment = re.search(r'&sqlText\s*=\s*(.*?);\s*\n&cursor', code, re.S).group(1)
        sql = ''.join(re.findall(r'"([^"\n]*)"', assignment))
        projection = re.search(r'^SELECT (.*?) FROM %Table\(GM_DEPT_TMP\)', sql).group(1)
        projection = re.sub(r"TO_CHAR\((\w+), '[^']+'\)", r'\1', projection)
        self.assertEqual([column.strip() for column in projection.split(',')], self.columns)
        self.assertIn('WHERE PROCESS_INSTANCE = :1 ORDER BY SETID, DEPTID, EFFDT', sql)
        self.assertIn('CreateSQL(&sqlText, &aet.PROCESS_INSTANCE.Value)', code)
        for filename in ['temp_export_peoplecode.pcode', 'export_peoplecode.pcode']:
            self.assertEqual((self.root / filename).read_text(encoding='utf-8'), code)


if __name__ == '__main__':
    unittest.main()
