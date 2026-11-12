"""카테고리 업무 규칙. 사용 중 삭제 판단은 저장소 밖에서 수행한다."""

from contextlib import closing

from budget_app.common.decorators import timed
from budget_app.common.errors import ConflictError, NotFoundError
from budget_app.domain.validation import category_name
from budget_app.infrastructure.repositories.categories import CategoryRepository
from budget_app.infrastructure.repositories.transactions import TransactionRepository


class CategoryService:
    def __init__(self, categories: CategoryRepository, transactions: TransactionRepository) -> None:
        self.categories = categories
        self.transactions = transactions

    def list_all(self) -> list[str]:
        return self.categories.list_all()

    @timed
    def add(self, name: str) -> str:
        name = category_name(name)
        with self.categories.store.write_lock():
            names = self.categories.list_all()
            if name in names:
                raise ConflictError(f'이미 등록된 카테고리: {name}', '다른 이름을 사용하거나 기존 카테고리를 선택하세요.')
            self.categories.save_all(names + [name])
        return name

    @timed
    def remove(self, name: str) -> str:
        name = category_name(name)
        with self.categories.store.write_lock():
            names = self.categories.list_all()
            if name not in names:
                raise NotFoundError(f'없는 카테고리: {name}', 'category list로 등록된 이름을 확인하세요.')
            with closing(self.transactions.iter_all()) as transactions:
                if any(transaction.category == name for transaction in transactions):
                    raise ConflictError(f'사용 중인 카테고리: {name}', '해당 거래의 카테고리를 수정하거나 거래를 삭제한 뒤 재시도하세요.')
            self.categories.save_all([value for value in names if value != name])
        return name
