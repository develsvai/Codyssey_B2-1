"""월별 집계. 거래/예산 서비스를 호출하지 않고 저장소를 조합한다."""

from collections import defaultdict
from contextlib import closing

from budget_app.common.decorators import timed
from budget_app.domain.reports import MonthlySummary
from budget_app.domain.validation import positive_int, valid_month
from budget_app.infrastructure.repositories.budgets import BudgetRepository
from budget_app.infrastructure.repositories.transactions import TransactionRepository


class ReportService:
    def __init__(self, transactions: TransactionRepository, budgets: BudgetRepository) -> None:
        self.transactions = transactions
        self.budgets = budgets

    @timed
    def monthly(self, month: str, top: int = 5) -> MonthlySummary:
        valid_month(month)
        top = positive_int(top, 'TOP 개수')
        income = expense = count = 0
        category_expenses: dict[str, int] = defaultdict(int)
        with closing(self.transactions.iter_all()) as transactions:
            for transaction in transactions:
                if transaction.date[:7] != month:
                    continue
                count += 1
                if transaction.type == 'income':
                    income += transaction.amount
                else:
                    expense += transaction.amount
                    category_expenses[transaction.category] += transaction.amount
        ranking = sorted(category_expenses.items(), key=lambda item: (-item[1], item[0]))[:top]
        return MonthlySummary(month, count, income, expense, tuple(ranking), self.budgets.get(month))
