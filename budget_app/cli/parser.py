"""공통 옵션과 기능별 명령의 등록."""

import argparse

from budget_app.cli.commands import budgets, categories, reports, transactions, transfer
from budget_app.common.errors import ValidationError


class CommandParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        kwargs.update(add_help=False, allow_abbrev=False)
        super().__init__(*args, **kwargs)
        self.add_argument('--help', action='help', help='사용 방법 표시')
        self.add_argument('--data-dir', default=argparse.SUPPRESS, help='저장 폴더 (기본: ./data)')
        self.add_argument('--verbose', action='store_true', default=argparse.SUPPRESS, help='실행 시간 로그 표시')

    def error(self, message: str) -> None:
        raise ValidationError(message, f'{self.prog} --help로 명령과 옵션을 확인하세요.')


def build_parser() -> CommandParser:
    parser = CommandParser(prog='python -m budget_app', description='나만의 콘솔 용돈 기입장')
    parser.set_defaults(data_dir='./data', verbose=False)
    commands = parser.add_subparsers(dest='command', required=True)
    for module in (transactions, categories, budgets, reports, transfer):
        module.register(commands)
    return parser
