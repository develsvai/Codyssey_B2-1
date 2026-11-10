"""CSV 가져오기/내보내기의 업무 절차와 검증."""

import calendar
from contextlib import closing
from pathlib import Path
from typing import Iterator
from uuid import uuid4

from budget_app.common.decorators import timed
from budget_app.common.errors import ValidationError
from budget_app.domain.models import Transaction
from budget_app.domain.queries import TransactionFilter
from budget_app.domain.validation import parse_tags, positive_int, registered_category, valid_month
from budget_app.infrastructure.csv_io import read_csv, write_csv
from budget_app.infrastructure.repositories.categories import CategoryRepository
from budget_app.infrastructure.repositories.transactions import TransactionRepository


class TransferService:
    def __init__(self, transactions: TransactionRepository, categories: CategoryRepository) -> None:
        self.transactions = transactions
        self.categories = categories

    @timed
    def import_csv(self, source: str | Path) -> int:
        path = Path(source).expanduser().resolve()
        with self.transactions.store.write_lock():
            categories = set(self.categories.list_all())
            batch = uuid4().hex
            def validated() -> Iterator[Transaction]:
                with closing(read_csv(path)) as rows:
                    for index, (number, row) in enumerate(rows, 1):
                        try:
                            yield Transaction(
                                f'TX-{batch}-{index:010d}', row['type'].strip(), row['date'].strip(),
                                positive_int(row['amount'].strip()), registered_category(row['category'], categories),
                                row.get('memo', ''), parse_tags(row.get('tags', '')),
                            )
                        except ValidationError as exc:
                            raise ValidationError(f'CSV {number}행: {exc}', exc.hint) from exc
            with closing(validated()) as transactions:
                return self.transactions.insert_many(transactions)

    @timed
    def export_csv(self, destination: str | Path, *, month: str | None = None,
                   start: str | None = None, end: str | None = None) -> int:
        if month is not None:
            if start is not None or end is not None:
                raise ValidationError('월과 기간 조건을 동시에 지정했습니다.', '--month 또는 --from/--to 쌍 중 하나를 사용하세요.')
            valid_month(month)
            year, month_number = map(int, month.split('-'))
            start, end = month + '-01', f'{month}-{calendar.monthrange(year, month_number)[1]:02d}'
        elif start is None or end is None:
            raise ValidationError('내보낼 기간이 필요합니다.', '--month 또는 --from과 --to를 함께 지정하세요.')
        query = TransactionFilter(start=start, end=end)
        path = Path(destination).expanduser().resolve()
        store = self.transactions.store
        protected = {store.path(name) for name in ('transactions', 'categories', 'budgets')}
        protected.add(store.root / '.write.lock')
        if path in protected:
            raise ValidationError('저장 파일을 CSV로 덮어쓸 수 없습니다.', '별도의 .csv 출력 경로를 지정하세요.')
        with closing(self.transactions.iter_all()) as transactions:
            return write_csv(path, (transaction for transaction in transactions if query.matches(transaction)))
