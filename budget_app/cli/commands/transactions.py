"""거래 명령의 입력을 서비스 호출로 연결한다."""

import argparse
from contextlib import closing

from budget_app.cli.context import Services
from budget_app.cli.presenters import message, show_categories, show_transactions
from budget_app.cli.prompts import ask, ask_text
from budget_app.common.errors import ValidationError
from budget_app.domain.queries import TransactionFilter
from budget_app.domain.validation import parse_tags, positive_int, registered_category, valid_date, valid_type


def add(args: argparse.Namespace, services: Services) -> None:
    categories = services.categories.list_all()
    if not categories:
        raise ValidationError('등록된 카테고리가 없습니다.', 'category add를 먼저 실행하세요.')
    date = ask('날짜(YYYY-MM-DD): ', valid_date)
    kind = ask('타입(income/expense): ', valid_type)
    show_categories(categories)
    category = ask('카테고리: ', lambda value: registered_category(value, categories))
    amount = ask('금액(양수 정수): ', positive_int)
    memo = ask_text('메모(선택): ')
    tags = parse_tags(ask_text('태그(쉼표로 구분, 없으면 엔터): '))
    transaction = services.transactions.add(date=date, type=kind, category=category, amount=amount, memo=memo, tags=tags)
    message(f'[저장 완료] id={transaction.id}')


def list_recent(args: argparse.Namespace, services: Services) -> None:
    with closing(services.transactions.list_recent(args.limit)) as transactions:
        show_transactions(transactions)


def search(args: argparse.Namespace, services: Services) -> None:
    query = TransactionFilter(args.start, args.end, args.category, args.type, args.q, args.tag)
    with closing(services.transactions.search(query)) as transactions:
        show_transactions(transactions)


def update(args: argparse.Namespace, services: Services) -> None:
    transaction = services.transactions.update(args.id, date=args.date, type=args.type, category=args.category,
        amount=args.amount, memo=args.memo, tags=parse_tags(args.tags) if args.tags is not None else None)
    message(f'[수정 완료] id={transaction.id}')


def delete(args: argparse.Namespace, services: Services) -> None:
    services.transactions.delete(args.id)
    message(f'[삭제 완료] id={args.id}')


def register(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser('add', help='대화형 거래 추가')
    parser.set_defaults(handler=add)
    parser = commands.add_parser('list', help='최신순 거래 목록')
    parser.add_argument('--limit', type=positive_int, default=20, help='조회 개수 (기본: 20)')
    parser.set_defaults(handler=list_recent)
    parser = commands.add_parser('search', help='조건별 거래 검색 (AND)')
    parser.add_argument('--from', dest='start', help='시작일 YYYY-MM-DD, 포함')
    parser.add_argument('--to', dest='end', help='종료일 YYYY-MM-DD, 포함')
    parser.add_argument('--category', help='등록된 카테고리')
    parser.add_argument('--type', choices=('income', 'expense'), help='거래 타입')
    parser.add_argument('--q', help='메모 키워드')
    parser.add_argument('--tag', help='정확히 일치하는 태그')
    parser.set_defaults(handler=search)
    parser = commands.add_parser('update', help='ID와 옵션으로 거래 수정')
    parser.add_argument('--id', required=True, help='거래 ID')
    parser.add_argument('--date', help='날짜 YYYY-MM-DD')
    parser.add_argument('--type', choices=('income', 'expense'), help='거래 타입')
    parser.add_argument('--category', help='등록된 카테고리')
    parser.add_argument('--amount', type=positive_int, help='양수 정수 금액')
    parser.add_argument('--memo', help='새 메모, 빈 문자열로 지우기')
    parser.add_argument('--tags', help='쉼표 구분 태그, 빈 문자열로 지우기')
    parser.set_defaults(handler=update)
    parser = commands.add_parser('delete', help='ID로 거래 삭제')
    parser.add_argument('--id', required=True, help='거래 ID')
    parser.set_defaults(handler=delete)
