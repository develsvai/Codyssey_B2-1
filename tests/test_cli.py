import csv
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = self.root / 'data'

    def run_cli(self, *arguments, input=''):
        return subprocess.run([sys.executable, '-m', 'budget_app', '--data-dir', str(self.data), *arguments],
                              cwd=ROOT, input=input, text=True, capture_output=True, timeout=15)

    def add(self, amount='15000', day='2024-01-15', kind='expense', category='food'):
        result = self.run_cli('add', input=f'{day}\n{kind}\n{category}\n{amount}\n점심\nmeal,식사\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        return re.search(r'id=(TX-\S+)', result.stdout).group(1)

    def test_help_for_every_command_has_no_storage_side_effect(self):
        commands = [(), ('add',), ('list',), ('search',), ('update',), ('delete',), ('summary',), ('import',), ('export',),
                    ('category',), ('category', 'add'), ('category', 'list'), ('category', 'remove'),
                    ('budget',), ('budget', 'set'), ('budget', 'show')]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_cli(*command, '--help')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('--help', result.stdout)
        self.assertFalse(self.data.exists())

    def test_add_list_search_update_delete(self):
        identifier = self.add()
        self.assertIn(identifier, self.run_cli('list', '--limit', '1').stdout)
        result = self.run_cli('search', '--from', '2024-01-15', '--to', '2024-01-15', '--category', 'food', '--type', 'expense', '--q', '점심', '--tag', 'meal')
        self.assertIn(identifier, result.stdout)
        self.assertEqual(self.run_cli('update', '--id', identifier, '--amount', '20000', '--memo', '', '--tags', '').returncode, 0)
        row = json.loads((self.data / 'transactions.jsonl').read_text())
        self.assertEqual((row['amount'], row['memo'], row['tags']), (20000, '', []))
        self.assertEqual(self.run_cli('delete', '--id', identifier).returncode, 0)
        self.assertIn('데이터 없음', self.run_cli('list').stdout)

    def test_interactive_reprompt(self):
        result = self.run_cli('add', input='bad\n2024-01-01\nwrong\nexpense\nmissing\nfood\n0\n100\n\n\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.count('[오류]'), 4)
        self.assertIn('[저장 완료]', result.stdout)

    def test_eof_cancels_without_transaction(self):
        result = self.run_cli('add', input='2024-01-01\n')
        self.assertEqual(result.returncode, 130)
        self.assertEqual((self.data / 'transactions.jsonl').read_text(), '')
        self.assertNotIn('Traceback', result.stderr)

    def test_budget_summary_warning_and_empty_month(self):
        self.add(amount='15000')
        self.assertEqual(self.run_cli('budget', 'set', '--month', '2024-01', '--amount', '10000').returncode, 0)
        result = self.run_cli('summary', '--month', '2024-01', '--top', '1')
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ['총 지출: 15000원', '잔액: -15000원', '150.0%', '[경고]', 'food 15000원']:
            self.assertIn(expected, result.stdout)
        self.assertIn('10000원', self.run_cli('budget', 'show', '--month', '2024-01').stdout)
        self.assertIn('데이터 없음', self.run_cli('summary', '--month', '2024-02').stdout)

    def test_category_interactive_and_used_removal(self):
        self.assertEqual(self.run_cli('category', 'add', input='취미\n').returncode, 0)
        self.assertIn('취미', self.run_cli('category', 'list').stdout)
        self.assertEqual(self.run_cli('category', 'remove', '--name', '취미').returncode, 0)
        self.add()
        result = self.run_cli('category', 'remove', '--name', 'food')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('사용 중', result.stderr)

    def test_csv_commands(self):
        self.add()
        csv_path = self.root / 'export.csv'
        result = self.run_cli('export', '--out', str(csv_path), '--month', '2024-01')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('1 records', result.stdout)
        result = self.run_cli('import', '--from', str(csv_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('imported=1', result.stdout)

    def test_export_combined_conditions(self):
        for day in ('2024-01-01', '2024-01-15', '2024-02-01'):
            self.add(day=day)
        csv_path = self.root / 'intersection.csv'
        result = self.run_cli('export', '--out', str(csv_path), '--month', '2024-01',
                              '--from', '2024-01-15', '--to', '2024-02-01')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('1 records', result.stdout)
        with csv_path.open(encoding='utf-8', newline='') as stream:
            self.assertEqual([row['date'] for row in csv.DictReader(stream)], ['2024-01-15'])
        result = self.run_cli('export', '--out', str(csv_path), '--month', '2024-01',
                              '--from', '2024-02-01', '--to', '2024-02-29')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('0 records', result.stdout)
        self.assertEqual(len(csv_path.read_text().splitlines()), 1)
        self.assertIn('교집합', self.run_cli('export', '--help').stdout)

    def test_invalid_arguments_errors_and_no_traceback(self):
        for args in [(), ('unknown',), ('list', '--limit', '0'), ('delete',), ('delete', '--id', 'missing'),
                     ('update', '--id', 'missing'), ('summary', '--month', '2024-13'), ('list', '--lim', '1'),
                     ('export', '--out', str(self.root / 'x.csv'))]:
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('[오류]', result.stderr)
                self.assertIn('[힌트]', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_data_dir_after_nested_command_and_verbose(self):
        other = self.root / 'other'
        result = self.run_cli('budget', 'set', '--data-dir', str(other), '--month', '2024-01', '--amount', '100', '--verbose')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.data.exists())
        self.assertTrue((other / 'budgets.jsonl').exists())
        self.assertIn('BudgetService.set', result.stderr)

    def test_corrupt_file_and_bad_directory(self):
        self.run_cli('list')
        (self.data / 'transactions.jsonl').write_text('broken\n')
        result = self.run_cli('list')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('JSONL', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        occupied = self.root / 'file'
        occupied.write_text('occupied')
        result = self.run_cli('list', '--data-dir', str(occupied))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stderr)
