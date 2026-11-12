"""불변 데이터 모델. 생성 시 형식 불변식을 보장한다."""

from dataclasses import dataclass

from budget_app.common.errors import ValidationError
from budget_app.domain.validation import category_name, positive_int, valid_date, valid_month, valid_type


@dataclass(frozen=True)
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ''
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValidationError('거래 ID가 비어 있습니다.', '앱이 생성한 ID를 사용하세요.')
        valid_type(self.type)
        valid_date(self.date)
        if type(self.amount) is not int:
            raise ValidationError('금액은 정수여야 합니다.', '양수 정수를 사용하세요.')
        positive_int(self.amount)
        if category_name(self.category) != self.category:
            raise ValidationError('카테고리에 앞뒤 공백이 있습니다.', '공백을 제거하세요.')
        if not isinstance(self.memo, str):
            raise ValidationError('메모는 문자열이어야 합니다.', '문자열 메모를 사용하세요.')
        if not isinstance(self.tags, tuple) or any(
            not isinstance(tag, str) or not tag.strip() or tag != tag.strip() or ',' in tag
            for tag in self.tags
        ):
            raise ValidationError('태그가 올바르지 않습니다.', '쉼표 없는 태그 문자열의 튜플을 사용하세요.')

    @property
    def sort_key(self) -> tuple[str, str]:
        return self.date, self.id


@dataclass(frozen=True)
class Budget:
    month: str
    amount: int

    def __post_init__(self) -> None:
        valid_month(self.month)
        if type(self.amount) is not int:
            raise ValidationError('예산은 정수여야 합니다.', '양수 정수를 사용하세요.')
        positive_int(self.amount, '예산')
