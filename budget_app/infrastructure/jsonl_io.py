"""JSONL 한 줄씩 읽기와 공통 안전 쓰기."""

import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from budget_app.common.errors import StorageError
from budget_app.infrastructure.atomic_file import atomic_text_writer


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    try:
        with path.open(encoding='utf-8') as stream:
            for number, line in enumerate(stream, 1):
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError('객체가 아닌 JSON')
                except (ValueError, TypeError) as exc:
                    raise StorageError(f'손상된 JSONL: {path}, {number}행', '원본을 보관하고 해당 행을 복구한 뒤 다시 실행하세요.') from exc
                yield row
    except (OSError, UnicodeError) as exc:
        raise StorageError(f'파일 읽기 실패: {path} ({exc})', '파일 존재 여부·읽기 권한·UTF-8 인코딩을 확인하세요.') from exc


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with atomic_text_writer(path) as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
