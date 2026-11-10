"""화면 문자열 대신 반환하는 월별 요약 결과."""

from dataclasses import dataclass
from decimal import Decimal

from budget_app.domain.models import Budget


@dataclass(frozen=True)
class MonthlySummary:
    month: str
    count: int
    income: int
    expense: int
    top_expenses: tuple[tuple[str, int], ...]
    budget: Budget | None

    @property
    def balance(self) -> int:
        return self.income - self.expense

    @property
    def usage_percent(self) -> Decimal | None:
        if self.budget is None:
            return None
        return Decimal(self.expense) * 100 / Decimal(self.budget.amount)

    @property
    def exceeded(self) -> bool:
        return self.budget is not None and self.expense > self.budget.amount
