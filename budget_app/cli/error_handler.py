"""업무 오류를 화면과 종료 코드로 바꾸는 CLI 전용 데코레이터."""

from functools import wraps
from typing import Callable, ParamSpec

from budget_app.cli.presenters import show_error
from budget_app.common.errors import AppError

P = ParamSpec('P')


def handle_errors(function: Callable[P, int]) -> Callable[P, int]:
    @wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> int:
        try:
            return function(*args, **kwargs)
        except AppError as exc:
            show_error(str(exc), exc.hint)
            return 2
        except (EOFError, KeyboardInterrupt):
            show_error('입력이 취소되었습니다.', '필요한 입력을 준비하고 명령을 다시 실행하세요.')
            return 130
        except (OSError, UnicodeError) as exc:
            show_error(f'입출력 실패: {exc}', '파일 경로·권한·디스크 공간·인코딩을 확인하세요.')
            return 1
        except Exception as exc:
            show_error(f'처리 실패 ({type(exc).__name__}): {exc}', '입력과 저장 파일을 확인하고 재현 명령으로 문제를 보고하세요.')
            return 1
    return wrapped
