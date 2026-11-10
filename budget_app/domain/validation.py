"""입력 표현과 저장 방식으로부터 독립된 검증 규칙."""

import re
from datetime import date
from typing import Iterable

from budget_app.common.errors import ValidationError


def valid_date(value: str) -> str:
    try:
        if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
            raise ValueError
        date.fromisoformat(value)
    except ValueError:
        raise ValidationError('날짜가 올바르지 않습니다.', '실제 날짜를 YYYY-MM-DD 형식으로 입력하세요.') from None
    return value


def valid_month(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}', value):
        raise ValidationError('월 형식이 올바르지 않습니다.', 'YYYY-MM 형식으로 입력하세요.')
    valid_date(value + '-01')
    return value


def positive_int(value: object, label: str = '금액') -> int:
    if isinstance(value, str) and re.fullmatch(r'[0-9]+', value):
        try:
            value = int(value)
        except ValueError:
            pass
    if type(value) is not int or value <= 0:
        raise ValidationError(f'{label}은 양수 정수여야 합니다.', '0보다 큰 정수를 입력하세요.')
    return value


def valid_type(value: str) -> str:
    if value not in ('income', 'expense'):
        raise ValidationError('거래 타입이 올바르지 않습니다.', 'income 또는 expense를 입력하세요.')
    return value


def category_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValidationError('카테고리명이 올바르지 않습니다.', '비어 있지 않은 한 줄 이름을 입력하세요.')
    return value.strip()


def registered_category(value: str, categories: Iterable[str]) -> str:
    name = category_name(value)
    if name not in categories:
        raise ValidationError(f'등록되지 않은 카테고리: {name}', 'category list로 확인하거나 category add로 등록하세요.')
    return name


def parse_tags(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(tag.strip() for tag in value.split(',') if tag.strip()))


def date_range(start: str | None, end: str | None) -> None:
    if start is not None:
        valid_date(start)
    if end is not None:
        valid_date(end)
    if start is not None and end is not None and start > end:
        raise ValidationError('시작일이 종료일보다 늦습니다.', '--from을 --to 이전 또는 같은 날짜로 지정하세요.')
