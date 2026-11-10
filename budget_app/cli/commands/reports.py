"""월별 요약 명령."""

import argparse

from budget_app.cli.context import Services
from budget_app.cli.presenters import show_summary
from budget_app.domain.validation import positive_int


def run(args: argparse.Namespace, services: Services) -> None:
    show_summary(services.reports.monthly(args.month, args.top), args.top)


def register(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser('summary', help='월별 수입·지출·예산 요약')
    parser.add_argument('--month', required=True, help='월 YYYY-MM')
    parser.add_argument('--top', type=positive_int, default=5, help='지출 순위 개수 (기본: 5)')
    parser.set_defaults(handler=run)
