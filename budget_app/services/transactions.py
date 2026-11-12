"""거래 CRUD와 스트리밍 조회. CLI 및 다른 서비스에 의존하지 않는다."""

from contextlib import closing
from dataclasses import replace
from itertools import islice
from typing import Iterator
from uuid import uuid4

from budget_app.common.decorators import timed
from budget_app.common.errors import ValidationError
from budget_app.domain.models import Transaction
from budget_app.domain.queries import TransactionFilter
from budget_app.domain.validation import category_name, positive_int, registered_category
from budget_app.infrastructure.repositories.categories import CategoryRepository
from budget_app.infrastructure.repositories.transactions import TransactionRepository


class TransactionService:
    def __init__(self, transactions: TransactionRepository, categories: CategoryRepository) -> None:
        self.transactions = transactions
        self.categories = categories

    @timed
    def add(self, *, date: str, type: str, category: str, amount: int | str,
            memo: str = '', tags: tuple[str, ...] = ()) -> Transaction:
        transaction = Transaction('TX-' + uuid4().hex, type, date, positive_int(amount), category_name(category), memo, tags)
        with self.transactions.store.write_lock():
            registered_category(transaction.category, self.categories.list_all())
            self.transactions.insert(transaction)
        return transaction

    @timed
    def update(self, identifier: str, *, date: str | None = None, type: str | None = None,
               category: str | None = None, amount: int | str | None = None,
               memo: str | None = None, tags: tuple[str, ...] | None = None) -> Transaction:
        changes = {key: value for key, value in dict(date=date, type=type, category=category,
                   amount=amount, memo=memo, tags=tags).items() if value is not None}
        if not changes:
            raise ValidationError('수정할 필드가 없습니다.', '--date, --type, --category, --amount, --memo, --tags 중 하나를 지정하세요.')
        if amount is not None:
            changes['amount'] = positive_int(amount)
        if category is not None:
            changes['category'] = category_name(category)
        with self.transactions.store.write_lock():
            original = self.transactions.get(identifier)
            updated = replace(original, **changes)
            registered_category(updated.category, self.categories.list_all())
            self.transactions.replace(updated)
        return updated

    @timed
    def delete(self, identifier: str) -> None:
        with self.transactions.store.write_lock():
            self.transactions.delete(identifier)

    def list_recent(self, limit: int = 20) -> Iterator[Transaction]:
        limit = positive_int(limit, '조회 개수')
        def records() -> Iterator[Transaction]:
            with closing(self.transactions.iter_all()) as transactions:
                yield from islice(transactions, limit)
        return records()

    def search(self, query: TransactionFilter) -> Iterator[Transaction]:
        if query.category is not None:
            registered_category(query.category, self.categories.list_all())
        def records() -> Iterator[Transaction]:
            with closing(self.transactions.iter_all()) as transactions:
                for transaction in transactions:
                    if query.matches(transaction):
                        yield transaction
        return records()
