from decimal import Decimal

from budget_app.common.errors import ValidationError
from budget_app.domain.models import Budget
from budget_app.services.reports import ReportService
from tests.support import StoreCase


class ReportTests(StoreCase):
    def setUp(self):
        super().setUp()
        self.service = ReportService(self.transactions, self.budgets)

    def test_totals_ranking_month_and_usage(self):
        self.seed(self.transaction('A', amount=3000, kind='income', category='salary'),
                  self.transaction('B', amount=200, category='food'),
                  self.transaction('C', amount=300, category='rent'),
                  self.transaction('D', amount=100, category='food'),
                  self.transaction('E', day='2024-02-01', amount=999))
        self.budgets.set(Budget('2024-01', 1000))
        summary = self.service.monthly('2024-01', top=1)
        self.assertEqual((summary.count, summary.income, summary.expense, summary.balance), (4, 3000, 600, 2400))
        self.assertEqual(summary.top_expenses, (('food', 300),))
        self.assertEqual(summary.usage_percent, Decimal('60'))
        self.assertFalse(summary.exceeded)

    def test_exact_budget_and_excess(self):
        self.seed(self.transaction(amount=100))
        self.budgets.set(Budget('2024-01', 100))
        self.assertFalse(self.service.monthly('2024-01').exceeded)
        self.budgets.set(Budget('2024-01', 99))
        self.assertTrue(self.service.monthly('2024-01').exceeded)

    def test_empty_month_and_unset_budget(self):
        summary = self.service.monthly('2024-01')
        self.assertEqual((summary.count, summary.income, summary.expense, summary.balance), (0, 0, 0, 0))
        self.assertIsNone(summary.usage_percent)
        self.assertEqual(summary.top_expenses, ())

    def test_empty_month_with_budget(self):
        self.budgets.set(Budget('2024-01', 100))
        self.assertEqual(self.service.monthly('2024-01').usage_percent, 0)

    def test_invalid_month_and_top(self):
        with self.assertRaises(ValidationError):
            self.service.monthly('2024-13')
        with self.assertRaises(ValidationError):
            self.service.monthly('2024-01', 0)
