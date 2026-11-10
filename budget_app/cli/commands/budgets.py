"""예산 명령."""

import argparse

from budget_app.cli.context import Services
from budget_app.cli.presenters import message, show_budget
from budget_app.domain.validation import positive_int


def run(args: argparse.Namespace, services: Services) -> None:
    if args.budget_command == 'set':
        budget = services.budgets.set(args.month, args.amount)
        message(f'[저장 완료] {budget.month} 예산 {budget.amount}원')
    else:
        show_budget(services.budgets.get(args.month))


def register(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser('budget', help='월 예산 설정·조회')
    subcommands = parser.add_subparsers(dest='budget_command', required=True)
    for action, description in [('set', '월 예산 설정'), ('show', '월 예산 조회')]:
        child = subcommands.add_parser(action, help=description)
        child.add_argument('--month', required=True, help='월 YYYY-MM')
        if action == 'set':
            child.add_argument('--amount', required=True, type=positive_int, help='양수 정수 예산')
        child.set_defaults(handler=run)
