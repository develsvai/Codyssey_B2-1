from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from budget_app.domain.models import Transaction
from budget_app.infrastructure.data_directory import DataDirectory
from budget_app.infrastructure.repositories.budgets import BudgetRepository
from budget_app.infrastructure.repositories.categories import CategoryRepository
from budget_app.infrastructure.repositories.transactions import TransactionRepository


class StoreCase(TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = DataDirectory(self.root / 'data')
        self.store.initialize()
        self.transactions = TransactionRepository(self.store)
        self.categories = CategoryRepository(self.store)
        self.budgets = BudgetRepository(self.store)

    def transaction(self, identifier='TX-1', day='2024-01-10', amount=100, category='food', kind='expense', memo='', tags=()):
        return Transaction(identifier, kind, day, amount, category, memo, tags)

    def seed(self, *transactions):
        with self.store.write_lock():
            for transaction in transactions:
                self.transactions.insert(transaction)
