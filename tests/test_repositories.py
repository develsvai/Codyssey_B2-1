import inspect
from dataclasses import replace
from unittest.mock import patch

from budget_app.common.errors import ConflictError, NotFoundError, StorageError
from budget_app.domain.models import Budget
from budget_app.infrastructure.data_directory import DataDirectory
from budget_app.infrastructure.jsonl_io import write_jsonl
from tests.support import StoreCase


class RepositoryTests(StoreCase):
    def test_initialization_and_empty_categories_are_preserved(self):
        self.assertEqual(len(list(self.store.root.glob('*.jsonl'))), 3)
        self.assertIn('food', self.categories.list_all())
        self.categories.save_all([])
        DataDirectory(self.store.root).initialize()
        self.assertEqual(self.categories.list_all(), [])

    def test_sorted_insert_update_delete_and_persistence(self):
        old = self.transaction('A', '2024-01-01')
        new = self.transaction('B', '2024-02-01')
        self.seed(old, new, self.transaction('C', '2024-02-01'))
        self.assertTrue(inspect.isgenerator(self.transactions.iter_all()))
        self.assertEqual([t.id for t in self.transactions.iter_all()], ['C', 'B', 'A'])
        with self.store.write_lock():
            self.transactions.replace(replace(old, date='2024-03-01'))
            self.transactions.delete('B')
        self.assertEqual([t.id for t in self.transactions.iter_all()], ['A', 'C'])
        self.assertEqual(self.transactions.get('A').date, '2024-03-01')

    def test_missing_ids_and_duplicate_leave_original(self):
        self.seed(self.transaction())
        before = self.transactions.path.read_bytes()
        for operation in [lambda: self.transactions.delete('missing'), lambda: self.transactions.replace(self.transaction('missing'))]:
            with self.assertRaises(NotFoundError):
                operation()
        with self.assertRaises(ConflictError):
            self.transactions.insert(self.transaction())
        self.assertEqual(self.transactions.path.read_bytes(), before)

    def test_failed_replace_preserves_original_and_cleans_temp(self):
        self.seed(self.transaction())
        before = self.transactions.path.read_bytes()
        with patch('budget_app.infrastructure.atomic_file.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(StorageError):
                self.transactions.insert(self.transaction('NEW'))
        self.assertEqual(self.transactions.path.read_bytes(), before)
        self.assertEqual(list(self.store.root.glob('*.tmp')), [])

    def test_generator_error_rolls_back(self):
        before = self.transactions.path.read_bytes()
        def broken():
            yield {'id': 'partial'}
            raise ValueError('bad input')
        with self.assertRaises(ValueError):
            write_jsonl(self.transactions.path, broken())
        self.assertEqual(self.transactions.path.read_bytes(), before)

    def test_corrupt_data_is_not_overwritten(self):
        self.transactions.path.write_text('{bad json}\n', encoding='utf-8')
        before = self.transactions.path.read_bytes()
        with self.assertRaises(StorageError):
            self.transactions.insert(self.transaction())
        self.assertEqual(self.transactions.path.read_bytes(), before)

    def test_rejects_unsorted_storage(self):
        from dataclasses import asdict
        write_jsonl(self.transactions.path, [asdict(self.transaction('A', '2024-01-01')), asdict(self.transaction('B', '2024-02-01'))])
        with self.assertRaises(StorageError):
            list(self.transactions.iter_all())

    def test_mutual_exclusion_and_lock_cleanup(self):
        other = DataDirectory(self.store.root)
        with self.store.write_lock():
            with self.assertRaises(ConflictError), other.write_lock():
                pass
        with self.assertRaises(ValueError), self.store.write_lock():
            raise ValueError('abort')
        self.assertFalse((self.store.root / '.write.lock').exists())

    def test_category_and_budget_persistence(self):
        self.categories.save_all(['food', '월급'])
        self.budgets.set(Budget('2024-01', 100))
        self.budgets.set(Budget('2024-02', 200))
        self.budgets.set(Budget('2024-01', 300))
        self.assertEqual(self.categories.list_all(), ['food', '월급'])
        self.assertEqual(self.budgets.get('2024-01').amount, 300)
        self.assertIsNone(self.budgets.get('2024-03'))
