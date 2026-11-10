import inspect
from unittest.mock import patch

from budget_app.common.errors import NotFoundError, ValidationError
from budget_app.domain.queries import TransactionFilter
from budget_app.services.transactions import TransactionService
from tests.support import StoreCase


class TransactionTests(StoreCase):
    def setUp(self):
        super().setUp()
        self.service = TransactionService(self.transactions, self.categories)

    def test_add_update_clear_and_delete(self):
        transaction = self.service.add(date='2024-01-01', type='expense', category='food', amount='100', memo='점심', tags=('meal',))
        self.assertTrue(transaction.id.startswith('TX-'))
        changed = self.service.update(transaction.id, date='2024-02-01', amount=200, memo='', tags=())
        self.assertEqual((changed.date, changed.amount, changed.memo, changed.tags), ('2024-02-01', 200, '', ()))
        self.service.delete(transaction.id)
        self.assertEqual(list(self.service.list_recent()), [])

    def test_bad_inputs_preserve_storage(self):
        fields = dict(date='2024-01-01', type='expense', category='food', amount=100)
        for change in [dict(date='2024-02-30'), dict(type='other'), dict(category='missing'), dict(amount=0)]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                self.service.add(**(fields | change))
        self.assertEqual(list(self.transactions.iter_all()), [])

    def test_invalid_update_and_missing_id(self):
        self.seed(self.transaction())
        before = self.transactions.path.read_bytes()
        for change in [dict(category='missing'), dict(amount=-1), {}]:
            with self.assertRaises(ValidationError):
                self.service.update('TX-1', **change)
        with self.assertRaises(NotFoundError):
            self.service.update('missing', amount=10)
        with self.assertRaises(NotFoundError):
            self.service.delete('missing')
        self.assertEqual(self.transactions.path.read_bytes(), before)

    def test_all_filters_combined_and_inclusive_dates(self):
        self.seed(self.transaction('A', memo='Lunch 점심', tags=('meal',)),
                  self.transaction('B', day='2024-01-11', category='transport'),
                  self.transaction('C', kind='income', category='salary'))
        query = TransactionFilter(start='2024-01-10', end='2024-01-10', category='food', type='expense', q='LUNCH', tag='meal')
        self.assertEqual([t.id for t in self.service.search(query)], ['A'])
        self.assertEqual([t.id for t in self.service.search(TransactionFilter(type='income'))], ['C'])
        self.assertEqual(list(self.service.search(TransactionFilter(tag='mea'))), [])
        self.assertEqual([t.id for t in self.service.search(TransactionFilter())], ['B', 'C', 'A'])

    def test_lazy_limit_does_not_read_remainder(self):
        def source():
            yield self.transaction()
            raise AssertionError('필요 이상으로 읽음')
        with patch.object(self.transactions, 'iter_all', side_effect=source):
            result = self.service.list_recent(1)
            self.assertTrue(inspect.isgenerator(result))
            self.assertEqual(len(list(result)), 1)

    def test_invalid_filters_and_limit(self):
        with self.assertRaises(ValidationError):
            TransactionFilter(start='2024-02-01', end='2024-01-01')
        with self.assertRaises(ValidationError):
            self.service.list_recent(0)
        with self.assertRaises(ValidationError):
            self.service.search(TransactionFilter(category='missing'))
