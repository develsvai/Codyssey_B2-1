"""등록 카테고리 저장소. 업무 규칙(사용 중 여부)은 서비스에서 판단한다."""

from budget_app.common.errors import StorageError, ValidationError
from budget_app.domain.validation import category_name
from budget_app.infrastructure.data_directory import DataDirectory
from budget_app.infrastructure.jsonl_io import read_jsonl, write_jsonl


class CategoryRepository:
    def __init__(self, store: DataDirectory) -> None:
        self.store = store
        self.path = store.path('categories')

    def list_all(self) -> list[str]:
        names: set[str] = set()
        for number, row in enumerate(read_jsonl(self.path), 1):
            try:
                name = category_name(row['name'])
                if name in names or name != row['name'] or set(row) != {'name'}:
                    raise ValueError('중복 또는 잘못된 이름')
            except (KeyError, ValueError, ValidationError) as exc:
                raise StorageError(f'잘못된 카테고리: {self.path}, {number}행', '카테고리 파일을 복구하세요.') from exc
            names.add(name)
        return sorted(names)

    def save_all(self, names: list[str]) -> None:
        write_jsonl(self.path, ({'name': name} for name in sorted(names)))
