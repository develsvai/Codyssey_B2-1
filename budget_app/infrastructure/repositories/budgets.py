"""월별 예산 저장소."""

from dataclasses import asdict

from budget_app.common.errors import StorageError, ValidationError
from budget_app.domain.models import Budget
from budget_app.infrastructure.data_directory import DataDirectory
from budget_app.infrastructure.jsonl_io import read_jsonl, write_jsonl


class BudgetRepository:
    def __init__(self, store: DataDirectory) -> None:
        self.store = store
        self.path = store.path('budgets')

    def list_all(self) -> list[Budget]:
        budgets: dict[str, Budget] = {}
        for number, row in enumerate(read_jsonl(self.path), 1):
            try:
                budget = Budget(**row)
                if budget.month in budgets:
                    raise ValueError('중복 월')
            except (TypeError, ValueError, ValidationError) as exc:
                raise StorageError(f'잘못된 예산: {self.path}, {number}행', '예산 파일을 복구하세요.') from exc
            budgets[budget.month] = budget
        return sorted(budgets.values(), key=lambda budget: budget.month, reverse=True)

    def get(self, month: str) -> Budget | None:
        return next((budget for budget in self.list_all() if budget.month == month), None)

    def set(self, budget: Budget) -> None:
        budgets = {item.month: item for item in self.list_all()}
        budgets[budget.month] = budget
        write_jsonl(self.path, (asdict(budgets[month]) for month in sorted(budgets, reverse=True)))
