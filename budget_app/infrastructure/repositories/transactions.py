"""날짜/ID 내림차순 JSONL 거래 저장소. 쓰기 호출자는 데이터 잠금을 잡는다."""

from contextlib import closing
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from budget_app.common.errors import ConflictError, NotFoundError, StorageError, ValidationError
from budget_app.domain.models import Transaction
from budget_app.infrastructure.data_directory import DataDirectory
from budget_app.infrastructure.jsonl_io import read_jsonl, write_jsonl


def decode_transaction(row: dict[str, Any], path: Path, number: int) -> Transaction:
    try:
        values = dict(row)
        tags = values.get('tags', [])
        if not isinstance(tags, list):
            raise ValueError('태그 배열이 아님')
        values['tags'] = tuple(tags)
        return Transaction(**values)
    except (TypeError, ValueError, ValidationError) as exc:
        raise StorageError(f'잘못된 거래 레코드: {path}, {number}행', '원본을 보관하고 필드 형식과 값을 복구하세요.') from exc


class TransactionRepository:
    def __init__(self, store: DataDirectory) -> None:
        self.store = store
        self.path = store.path('transactions')

    def iter_all(self) -> Iterator[Transaction]:
        previous: tuple[str, str] | None = None
        with closing(read_jsonl(self.path)) as rows:
            for number, row in enumerate(rows, 1):
                transaction = decode_transaction(row, self.path, number)
                if previous is not None and transaction.sort_key >= previous:
                    raise StorageError(f'거래 순서 또는 ID 중복 오류: {self.path}, {number}행', '날짜/ID 내림차순 원본을 복구하세요. 파일을 직접 편집하지 마세요.')
                previous = transaction.sort_key
                yield transaction

    def get(self, identifier: str) -> Transaction:
        with closing(self.iter_all()) as transactions:
            for transaction in transactions:
                if transaction.id == identifier:
                    return transaction
        raise NotFoundError(f'없는 거래 ID: {identifier}', 'list 또는 search로 거래 ID를 확인하세요.')

    def insert(self, transaction: Transaction) -> None:
        self._merge_one(transaction, replace_id=None)

    def replace(self, transaction: Transaction) -> None:
        self.get(transaction.id)
        self._merge_one(transaction, replace_id=transaction.id)

    def _merge_one(self, new: Transaction, replace_id: str | None) -> None:
        def records() -> Iterator[dict[str, Any]]:
            inserted = False
            with closing(self.iter_all()) as transactions:
                for old in transactions:
                    if old.id == new.id:
                        if replace_id is None:
                            raise ConflictError(f'중복 거래 ID: {new.id}', '새 ID로 다시 시도하세요.')
                        continue
                    if not inserted and new.sort_key > old.sort_key:
                        yield asdict(new)
                        inserted = True
                    yield asdict(old)
            if not inserted:
                yield asdict(new)
        write_jsonl(self.path, records())

    def delete(self, identifier: str) -> None:
        def records() -> Iterator[dict[str, Any]]:
            found = False
            with closing(self.iter_all()) as transactions:
                for transaction in transactions:
                    if transaction.id == identifier:
                        found = True
                    else:
                        yield asdict(transaction)
            if not found:
                raise NotFoundError(f'없는 거래 ID: {identifier}', 'list로 ID를 확인하세요.')
        write_jsonl(self.path, records())
