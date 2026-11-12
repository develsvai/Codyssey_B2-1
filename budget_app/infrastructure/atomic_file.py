"""같은 파일 시스템 안에서 완성된 파일만 원자적으로 공개한다."""

import os
from contextlib import contextmanager, suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator, TextIO

from budget_app.common.errors import StorageError


@contextmanager
def atomic_text_writer(path: Path) -> Iterator[TextIO]:
    temporary: Path | None = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', newline='', dir=path.parent,
                                prefix=f'.{path.name}.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except (OSError, UnicodeError) as exc:
        raise StorageError(f'파일 쓰기 실패: {path} ({exc})', '경로·쓰기 권한·디스크 공간을 확인하세요. 기존 파일은 교체 전까지 보존됩니다.') from exc
    finally:
        if temporary is not None:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
