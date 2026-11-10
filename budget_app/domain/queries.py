"""저장 방식과 무관한 거래 검색 조건."""

from dataclasses import dataclass

from budget_app.domain.models import Transaction
from budget_app.domain.validation import category_name, date_range, valid_type


@dataclass(frozen=True)
class TransactionFilter:
    start: str | None = None
    end: str | None = None
    category: str | None = None
    type: str | None = None
    q: str | None = None
    tag: str | None = None

    def __post_init__(self) -> None:
        date_range(self.start, self.end)
        if self.category is not None:
            category_name(self.category)
        if self.type is not None:
            valid_type(self.type)

    def matches(self, transaction: Transaction) -> bool:
        return (
            (self.start is None or transaction.date >= self.start)
            and (self.end is None or transaction.date <= self.end)
            and (self.category is None or transaction.category == self.category)
            and (self.type is None or transaction.type == self.type)
            and (self.q is None or self.q.casefold() in transaction.memo.casefold())
            and (self.tag is None or self.tag in transaction.tags)
        )
