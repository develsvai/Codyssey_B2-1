"""월 예산 설정·조회 서비스."""

from budget_app.common.decorators import timed
from budget_app.domain.models import Budget
from budget_app.domain.validation import positive_int, valid_month
from budget_app.infrastructure.repositories.budgets import BudgetRepository


class BudgetService:
    def __init__(self, budgets: BudgetRepository) -> None:
        self.budgets = budgets

    @timed
    def set(self, month: str, amount: int | str) -> Budget:
        budget = Budget(valid_month(month), positive_int(amount, '예산'))
        with self.budgets.store.write_lock():
            self.budgets.set(budget)
        return budget

    def get(self, month: str) -> Budget | None:
        return self.budgets.get(valid_month(month))
