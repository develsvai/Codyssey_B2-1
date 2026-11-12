"""대화형 입력과 재입력 루프를 한 곳에서 관리한다."""

from typing import Callable, TypeVar

from budget_app.cli.presenters import show_error
from budget_app.common.errors import ValidationError

T = TypeVar('T')


def ask(label: str, validator: Callable[[str], T]) -> T:
    while True:
        value = input(label).strip()
        try:
            return validator(value)
        except ValidationError as exc:
            show_error(str(exc), exc.hint)


def ask_text(label: str) -> str:
    return input(label)
