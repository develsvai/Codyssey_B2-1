from budget_app.common.errors import ValidationError
from budget_app.services.budgets import BudgetService
from tests.support import StoreCase


class BudgetTests(StoreCase):
    def setUp(self):
        super().setUp()
        self.service = BudgetService(self.budgets)

    def test_set_get_and_replace(self):
        self.service.set('2024-01', '100')
        self.service.set('2024-02', 200)
        self.service.set('2024-01', 300)
        self.assertEqual(self.service.get('2024-01').amount, 300)
        self.assertEqual(self.service.get('2024-02').amount, 200)
        self.assertEqual(len(self.budgets.list_all()), 2)

    def test_unset_month(self):
        self.assertIsNone(self.service.get('2024-01'))

    def test_invalid_budget_preserves_previous(self):
        self.service.set('2024-01', 100)
        before = self.budgets.path.read_bytes()
        for month, amount in [('2024-13', 1), ('2024-1', 1), ('2024-01', 0), ('2024-01', True), ('2024-01', '1.5')]:
            with self.subTest(month=month, amount=amount), self.assertRaises(ValidationError):
                self.service.set(month, amount)
        self.assertEqual(self.budgets.path.read_bytes(), before)
