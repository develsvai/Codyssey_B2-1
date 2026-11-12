"""CSV 입출력 명령."""

import argparse

from budget_app.cli.context import Services
from budget_app.cli.presenters import message, safe_text


def import_csv(args: argparse.Namespace, services: Services) -> None:
    count = services.transfer.import_csv(args.source)
    message(f'[완료] imported={count}, skipped=0')


def export_csv(args: argparse.Namespace, services: Services) -> None:
    count = services.transfer.export_csv(args.out, month=args.month, start=args.start, end=args.end)
    message(f'[완료] {safe_text(args.out)} ({count} records)')


def register(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser('import', help='UTF-8 CSV 가져오기 (오류 시 전체 취소)')
    parser.add_argument('--from', dest='source', required=True, help='CSV 입력 파일')
    parser.set_defaults(handler=import_csv)
    parser = commands.add_parser('export', help='월·기간별 UTF-8 CSV 내보내기 (함께 지정 시 교집합)')
    parser.add_argument('--out', required=True, help='CSV 출력 경로 (기존 파일 교체)')
    parser.add_argument('--month', help='월 YYYY-MM, 기간과 함께 지정하면 교집합')
    parser.add_argument('--from', dest='start', help='시작일 YYYY-MM-DD (--to와 함께)')
    parser.add_argument('--to', dest='end', help='종료일 YYYY-MM-DD (--from과 함께)')
    parser.set_defaults(handler=export_csv)
