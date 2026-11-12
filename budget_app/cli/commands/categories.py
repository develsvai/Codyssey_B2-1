"""카테고리 명령."""

import argparse

from budget_app.cli.context import Services
from budget_app.cli.presenters import message, show_categories
from budget_app.cli.prompts import ask
from budget_app.domain.validation import category_name


def run(args: argparse.Namespace, services: Services) -> None:
    if args.category_command == 'list':
        show_categories(services.categories.list_all())
        return
    name = args.name if args.name is not None else ask('카테고리명: ', category_name)
    if args.category_command == 'add':
        name = services.categories.add(name)
        message(f'[저장 완료] category={name}')
    else:
        name = services.categories.remove(name)
        message(f'[삭제 완료] category={name}')


def register(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser('category', help='카테고리 관리')
    subcommands = parser.add_subparsers(dest='category_command', required=True)
    for action, description in [('add', '카테고리 추가'), ('list', '카테고리 목록'), ('remove', '카테고리 삭제')]:
        child = subcommands.add_parser(action, help=description)
        if action != 'list':
            child.add_argument('--name', help='이름 (생략하면 대화형 입력)')
        child.set_defaults(handler=run)
