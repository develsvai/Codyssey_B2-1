"""저장 경로, 초기화, 여러 저장소를 묶는 쓰기 잠금."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from budget_app.common.errors import ConflictError, StorageError
from budget_app.infrastructure.jsonl_io import write_jsonl

DEFAULT_CATEGORIES = ('food', 'transport', 'rent', 'salary', 'etc')


class DataDirectory:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()

    def path(self, name: str) -> Path:
        return self.root / f'{name}.jsonl'

    @contextmanager
    def write_lock(self) -> Iterator[None]:
        lock_path = self.root / '.write.lock'
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            fd = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise ConflictError('다른 쓰기 작업의 잠금이 남아 있습니다.', f'다른 실행이 끝난 뒤 재시도하세요. 비정상 종료라면 실행 중인 앱이 없는지 확인 후 {lock_path}를 제거하세요.') from None
        except OSError as exc:
            raise StorageError(f'저장 폴더를 잠글 수 없습니다: {self.root}', '폴더 경로와 쓰기 권한을 확인하세요.') from exc
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                stream.write(str(os.getpid()))
            yield
        finally:
            lock_path.unlink(missing_ok=True)

    def initialize(self) -> None:
        names = ('transactions', 'categories', 'budgets')
        if all(self.path(name).is_file() for name in names):
            return
        with self.write_lock():
            for name in names:
                if not self.path(name).exists():
                    rows = ({'name': value} for value in DEFAULT_CATEGORIES) if name == 'categories' else ()
                    write_jsonl(self.path(name), rows)
