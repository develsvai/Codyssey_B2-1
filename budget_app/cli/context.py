"""CLI에 주입하는 기능 서비스 묶음. 객체 생성은 진입점이 담당한다."""

from dataclasses import dataclass

from budget_app.services.budgets import BudgetService
from budget_app.services.categories import CategoryService
from budget_app.services.reports import ReportService
from budget_app.services.transactions import TransactionService
from budget_app.services.transfer import TransferService


@dataclass(frozen=True)
class Services:
    transactions: TransactionService
    categories: CategoryService
    budgets: BudgetService
    reports: ReportService
    transfer: TransferService
