"""레코드와 열린 파일 수를 제한하는 디스크 병합 정렬."""

import heapq
from contextlib import ExitStack, closing
from itertools import islice
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, Iterable, Iterator

from budget_app.infrastructure.jsonl_io import read_jsonl, write_jsonl

CHUNK_SIZE = 1024
FAN_IN = 32


def external_sort(rows: Iterable[dict[str, Any]], directory: Path,
                  key: Callable[[dict[str, Any]], tuple[str, str]]) -> Iterator[dict[str, Any]]:
    with TemporaryDirectory(prefix='.import-', dir=directory) as folder:
        root = Path(folder)
        source = iter(rows)
        paths: list[Path] = []
        while chunk := list(islice(source, CHUNK_SIZE)):
            path = root / f'chunk-{len(paths)}.jsonl'
            write_jsonl(path, sorted(chunk, key=key, reverse=True))
            paths.append(path)
        generation = 0
        while len(paths) > 1:
            merged_paths: list[Path] = []
            for offset in range(0, len(paths), FAN_IN):
                group = paths[offset:offset + FAN_IN]
                output = root / f'merge-{generation}-{offset}.jsonl'
                with ExitStack() as stack:
                    readers = [stack.enter_context(closing(read_jsonl(path))) for path in group]
                    write_jsonl(output, heapq.merge(*readers, key=key, reverse=True))
                merged_paths.append(output)
                for path in group:
                    path.unlink()
            paths = merged_paths
            generation += 1
        if paths:
            yield from read_jsonl(paths[0])
