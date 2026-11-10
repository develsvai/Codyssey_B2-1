"""출력 방식에 의존하지 않는 실행 시간 측정."""

import logging
from functools import wraps
from time import perf_counter
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec('P')
R = TypeVar('R')
logger = logging.getLogger('budget_app.timing')


def timed(function: Callable[P, R]) -> Callable[P, R]:
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            logger.debug('%s %.6fs', function.__qualname__, perf_counter() - start)
    return wrapped
