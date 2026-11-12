"""실제 명령 프로세스와 큰 저장 파일을 사용한 인수 검증."""

import json
import subprocess
import sys
import tracemalloc
from pathlib import Path

from budget_app.domain.queries import TransactionFilter
from budget_app.infrastructure.jsonl_io import write_jsonl
from budget_app.services.transactions import TransactionService
from tests.support import StoreCase

ROOT = Path(__file__).resolve().parents[1]


class AcceptanceTests(StoreCase):
    def command(self, *args, data=None, expected=0):
        result = subprocess.run([sys.executable, '-m', 'budget_app', '--data-dir', str(data or self.store.root), *args],
                                cwd=ROOT, input='', text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, expected, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        return result

    def test_mission_scenario_across_processes_and_new_data_directory(self):
        incoming = self.root / 'mission.csv'
        incoming.write_text(
            'date,type,category,amount,memo,tags\n'
            '2024-01-14,income,salary,3000000,월급,\n'
            '2024-01-12,expense,transport,20000,교통,\n'
            '2024-01-15,expense,food,45000,점심,meal\n'
            '2024-01-01,expense,rent,150000,월세,\n', encoding='utf-8')
        self.assertIn('imported=4', self.command('import', '--from', str(incoming)).stdout)
        self.command('budget', 'set', '--month', '2024-01', '--amount', '500000')
        summary = self.command('summary', '--month', '2024-01', '--top', '3').stdout
        for expected in ['총 수입: 3000000원', '총 지출: 215000원', '잔액: 2785000원', '43.0%', '1) rent 150000원']:
            self.assertIn(expected, summary)
        self.command('category', 'remove', '--name', 'food', expected=2)
        rows = list(self.transactions.iter_all())
        rent = next(t for t in rows if t.category == 'rent')
        transport = next(t for t in rows if t.category == 'transport')
        self.command('update', '--id', rent.id, '--amount', '500000')
        self.assertIn('[경고]', self.command('summary', '--month', '2024-01').stdout)
        self.command('delete', '--id', transport.id)
        output = self.root / 'month.csv'
        self.assertIn('3 records', self.command('export', '--out', str(output), '--month', '2024-01').stdout)
        other = self.root / 'new-data'
        self.command('import', '--from', str(output), data=other)
        self.assertIn('총 지출: 545000원', self.command('summary', '--month', '2024-01', data=other).stdout)
        original = [json.loads(line) for line in self.transactions.path.read_text().splitlines()]
        copied = [json.loads(line) for line in (other / 'transactions.jsonl').read_text().splitlines()]
        self.assertTrue({row['id'] for row in original}.isdisjoint(row['id'] for row in copied))

    def test_writer_in_other_process_is_blocked_without_losing_data(self):
        before = self.budgets.path.read_bytes()
        with self.store.write_lock():
            result = self.command('budget', 'set', '--month', '2024-01', '--amount', '100', expected=2)
            self.assertIn('잠금', result.stderr)
        self.assertEqual(self.budgets.path.read_bytes(), before)
        self.command('budget', 'set', '--month', '2024-01', '--amount', '100')

    def test_large_search_streams_without_materializing_transactions(self):
        def rows():
            for index in range(12000, 0, -1):
                yield dict(id=f'TX-{index:08d}', date='2024-01-01', type='expense', category='food',
                           amount=1, memo='점심', tags=['meal'])
        write_jsonl(self.transactions.path, rows())
        service = TransactionService(self.transactions, self.categories)
        tracemalloc.start()
        try:
            count = sum(1 for _ in service.search(TransactionFilter(tag='meal')))
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(count, 12000)
        self.assertLess(peak, 1_000_000, f'스트리밍 중 최대 메모리 {peak} bytes')
