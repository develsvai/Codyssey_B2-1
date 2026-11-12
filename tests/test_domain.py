import unittest
from dataclasses import FrozenInstanceError

from budget_app.common.decorators import timed
from budget_app.common.errors import ValidationError
from budget_app.domain.models import Budget, Transaction
from budget_app.domain.validation import date_range, parse_tags, positive_int, registered_category, valid_date


class DomainTests(unittest.TestCase):
    def test_real_dates_and_strict_format(self):
        self.assertEqual(valid_date('2024-02-29'), '2024-02-29')
        for value in ['2023-02-29', '2024-13-01', '2024-1-01', '0000-01-01', '20240101']:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                valid_date(value)

    def test_positive_integer(self):
        self.assertEqual(positive_int('120'), 120)
        for value in [True, 0, -1, 1.2, '1.2', '', 'NaN', '+1']:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                positive_int(value)

    def test_immutable_transaction_and_bad_fields(self):
        values = dict(id='TX-1', type='expense', date='2024-01-01', amount=1, category='food')
        transaction = Transaction(**values)
        with self.assertRaises(FrozenInstanceError):
            transaction.amount = 2
        for field, value in [('type', 'other'), ('amount', True), ('amount', '1'), ('category', ''), ('tags', ('a,b',)), ('memo', None)]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                Transaction(**(values | {field: value}))

    def test_budget_and_category(self):
        self.assertEqual(Budget('2024-01', 100).amount, 100)
        for month in ['2024-13', '2024-1']:
            with self.assertRaises(ValidationError):
                Budget(month, 1)
        with self.assertRaises(ValidationError):
            registered_category('food', ['salary'])

    def test_range_and_tags(self):
        with self.assertRaises(ValidationError):
            date_range('2024-02-01', '2024-01-01')
        self.assertEqual(parse_tags(' meal, 점심,meal, '), ('meal', '점심'))

    def test_timed_preserves_result_metadata_and_errors(self):
        @timed
        def sample(value: int) -> int:
            if value < 0:
                raise ValueError('failure')
            return value * 2
        with self.assertLogs('budget_app.timing', level='DEBUG') as logs:
            self.assertEqual(sample(2), 4)
            with self.assertRaises(ValueError):
                sample(-1)
        self.assertEqual(sample.__name__, 'sample')
        self.assertEqual(len(logs.output), 2)
