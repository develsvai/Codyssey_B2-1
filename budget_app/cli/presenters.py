"""공통 화면 표현. 파일 저장이나 업무 계산을 하지 않는다."""

import sys
from typing import Iterable

from budget_app.domain.models import Budget, Transaction
from budget_app.domain.reports import MonthlySummary


def safe_text(value: object) -> str:
    return ''.join(character if character.isprintable() else repr(character)[1:-1] for character in str(value))


def message(text: str) -> None:
    print(text)


def show_error(message: str, hint: str) -> None:
    print(f'[오류] {safe_text(message)}\n[힌트] {safe_text(hint)}', file=sys.stderr)


def show_transactions(transactions: Iterable[Transaction]) -> None:
    found = False
    for transaction in transactions:
        if not found:
            print('ID | 날짜 | 타입 | 카테고리 | 금액 | 메모 | 태그')
            found = True
        print(' | '.join(safe_text(value) for value in (
            transaction.id, transaction.date, transaction.type, transaction.category,
            transaction.amount, transaction.memo, ','.join(transaction.tags))))
    if not found:
        print('데이터 없음')


def show_categories(names: list[str]) -> None:
    if not names:
        print('카테고리 없음. category add로 등록하세요.')
    for name in names:
        print(f'- {safe_text(name)}')


def show_budget(budget: Budget | None) -> None:
    if budget is None:
        print('설정된 예산 없음. budget set으로 설정하세요.')
    else:
        print(f'{budget.month} 예산: {budget.amount}원')


def show_summary(summary: MonthlySummary, top: int) -> None:
    print(f'월별 요약: {summary.month}')
    if summary.count == 0:
        print('데이터 없음')
    print(f'총 수입: {summary.income}원\n총 지출: {summary.expense}원\n잔액: {summary.balance}원')
    if summary.budget is not None:
        print(f'예산: {summary.budget.amount}원 (사용률 {summary.usage_percent:.1f}%)')
        if summary.exceeded:
            print('[경고] 예산을 초과했습니다.')
    print(f'지출 TOP {top}')
    for index, (name, amount) in enumerate(summary.top_expenses, 1):
        print(f'{index}) {safe_text(name)} {amount}원')
