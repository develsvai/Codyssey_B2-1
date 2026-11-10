"""CSV 표현과 파일 처리만 담당한다. 업무 검증은 서비스에서 수행한다."""

import csv
from pathlib import Path
from typing import Iterable, Iterator

from budget_app.common.errors import StorageError, ValidationError
from budget_app.domain.models import Transaction
from budget_app.infrastructure.atomic_file import atomic_text_writer

CSV_FIELDS = ('date', 'type', 'category', 'amount', 'memo', 'tags')
REQUIRED_FIELDS = frozenset(CSV_FIELDS[:4])


def read_csv(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    try:
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream, strict=True)
            fields = reader.fieldnames
            if (fields is None or len(fields) != len(set(fields))
                    or not REQUIRED_FIELDS.issubset(fields) or not set(fields).issubset(CSV_FIELDS)):
                raise ValidationError('CSV 헤더가 올바르지 않습니다.', '필수 date,type,category,amount와 선택 memo,tags 헤더만 사용하세요.')
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValidationError(f'CSV {reader.line_num}행의 열 수가 다릅니다.', '헤더에 맞추고 쉼표를 포함한 값은 큰따옴표로 감싸세요.')
                yield reader.line_num, row
    except csv.Error as exc:
        raise ValidationError(f'CSV 형식 오류: {path} ({exc})', '따옴표·쉼표와 필드 크기를 확인하세요.') from exc
    except (OSError, UnicodeError) as exc:
        raise StorageError(f'CSV 읽기 실패: {path} ({exc})', '경로·권한과 UTF-8 인코딩을 확인하세요.') from exc


def write_csv(path: Path, transactions: Iterable[Transaction]) -> int:
    count = 0
    with atomic_text_writer(path) as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(dict(date=transaction.date, type=transaction.type, category=transaction.category,
                                 amount=transaction.amount, memo=transaction.memo, tags=','.join(transaction.tags)))
            count += 1
    return count
