import csv
from dataclasses import replace
from unittest.mock import patch

from budget_app.common.errors import StorageError, ValidationError
from budget_app.services.transfer import TransferService
from tests.support import StoreCase


class TransferTests(StoreCase):
    def setUp(self):
        super().setUp()
        self.service = TransferService(self.transactions, self.categories)
        self.csv_path = self.root / 'exchange.csv'

    def write(self, content):
        self.csv_path.write_text(content, encoding='utf-8')

    def test_roundtrip_quotes_newlines_unicode_and_tags(self):
        original = self.transaction(memo='점심, "친구"\n다음 줄', tags=('meal', '식사'))
        self.seed(original)
        self.assertEqual(self.service.export_csv(self.csv_path, month='2024-01'), 1)
        self.assertEqual(self.service.import_csv(self.csv_path), 1)
        imported = next(t for t in self.transactions.iter_all() if t.id != original.id)
        self.assertEqual(replace(imported, id=original.id), original)

    def test_chunked_sort_multiple_merge_passes(self):
        with self.csv_path.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['date', 'type', 'category', 'amount'])
            for index in range(2300):
                writer.writerow([f'2024-01-{index % 28 + 1:02d}', 'expense', 'food', index + 1])
        self.seed(self.transaction('EXISTING', '2024-02-01'))
        with patch('budget_app.infrastructure.external_sort.CHUNK_SIZE', 64), patch('budget_app.infrastructure.external_sort.FAN_IN', 4):
            self.assertEqual(self.service.import_csv(self.csv_path), 2300)
        keys = [t.sort_key for t in self.transactions.iter_all()]
        self.assertEqual(keys, sorted(keys, reverse=True))
        self.assertEqual(len(keys), 2301)
        self.assertEqual(list(self.store.root.glob('.import-*')), [])

    def test_bad_late_row_rolls_back_all_imported_rows(self):
        self.seed(self.transaction())
        before = self.transactions.path.read_bytes()
        self.write('date,type,category,amount\n2024-01-01,expense,food,100\n2024-02-30,expense,food,200\n')
        with self.assertRaisesRegex(ValidationError, '3행'):
            self.service.import_csv(self.csv_path)
        self.assertEqual(self.transactions.path.read_bytes(), before)
        self.assertEqual(list(self.store.root.glob('.import-*')), [])

    def test_unknown_category_is_not_automatically_added(self):
        self.write('date,type,category,amount\n2024-01-01,expense,unknown,1\n')
        with self.assertRaisesRegex(ValidationError, '2행'):
            self.service.import_csv(self.csv_path)
        self.assertNotIn('unknown', self.categories.list_all())

    def test_invalid_headers_columns_and_csv_syntax(self):
        for content in ['', 'date,type,amount\n', 'date,type,category,amount,amount\n', 'date,type,category,amount,extra\n',
                        'date,type,category,amount\n2024-01-01,expense,food\n',
                        'date,type,category,amount\n2024-01-01,expense,food,1,extra\n',
                        'date,type,category,amount\n"unterminated']:
            self.write(content)
            with self.subTest(content=content), self.assertRaises(ValidationError):
                self.service.import_csv(self.csv_path)

    def test_bom_and_header_only(self):
        self.write('\ufeffdate,type,category,amount\n')
        self.assertEqual(self.service.import_csv(self.csv_path), 0)

    def test_export_conditions_inclusive_and_empty(self):
        self.seed(self.transaction('A', '2024-01-01'), self.transaction('B', '2024-01-31'), self.transaction('C', '2024-02-01'))
        self.assertEqual(self.service.export_csv(self.csv_path, start='2024-01-01', end='2024-01-31'), 2)
        self.assertEqual(self.service.export_csv(self.csv_path, month='2024-03'), 0)
        self.assertEqual(len(self.csv_path.read_text().splitlines()), 1)

    def test_export_requires_one_complete_condition(self):
        for options in [{}, {'start': '2024-01-01'}, {'month': '2024-01', 'end': '2024-01-31'},
                        {'month': '2024-13'}, {'start': '2024-02-01', 'end': '2024-01-01'}]:
            with self.subTest(options=options), self.assertRaises(ValidationError):
                self.service.export_csv(self.csv_path, **options)

    def test_prevent_export_over_live_data_or_alias(self):
        for name in ('transactions', 'categories', 'budgets'):
            path = self.store.path(name)
            before = path.read_bytes()
            with self.assertRaises(ValidationError):
                self.service.export_csv(path, month='2024-01')
            self.assertEqual(path.read_bytes(), before)
        alias = self.root / 'alias.csv'
        alias.symlink_to(self.transactions.path)
        with self.assertRaises(ValidationError):
            self.service.export_csv(alias, month='2024-01')

    def test_failed_export_preserves_existing_destination(self):
        self.write('keep original')
        with patch('budget_app.infrastructure.atomic_file.os.replace', side_effect=OSError('disk full')):
            with self.assertRaises(StorageError):
                self.service.export_csv(self.csv_path, month='2024-01')
        self.assertEqual(self.csv_path.read_text(), 'keep original')

    def test_missing_or_non_utf8_input(self):
        with self.assertRaises(StorageError):
            self.service.import_csv(self.csv_path)
        self.csv_path.write_bytes(b'\xff\xfe')
        with self.assertRaises(StorageError):
            self.service.import_csv(self.csv_path)
