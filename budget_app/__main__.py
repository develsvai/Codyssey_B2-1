"""실행 진입점 및 객체 조립. 하위 모듈은 이 모듈을 참조하지 않는다."""

import logging

from budget_app.cli.context import Services
from budget_app.cli.error_handler import handle_errors
from budget_app.cli.parser import build_parser
from budget_app.infrastructure.data_directory import DataDirectory
from budget_app.infrastructure.repositories.budgets import BudgetRepository
from budget_app.infrastructure.repositories.categories import CategoryRepository
from budget_app.infrastructure.repositories.transactions import TransactionRepository
from budget_app.services.budgets import BudgetService
from budget_app.services.categories import CategoryService
from budget_app.services.reports import ReportService
from budget_app.services.transactions import TransactionService
from budget_app.services.transfer import TransferService


def build_services(data_dir: str) -> Services:
    store = DataDirectory(data_dir)
    store.initialize()
    transactions = TransactionRepository(store)
    categories = CategoryRepository(store)
    budgets = BudgetRepository(store)
    return Services(TransactionService(transactions, categories), CategoryService(categories, transactions),
                    BudgetService(budgets), ReportService(transactions, budgets), TransferService(transactions, categories))


@handle_errors
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format='[로그] %(message)s')
    services = build_services(args.data_dir)
    args.handler(args, services)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
