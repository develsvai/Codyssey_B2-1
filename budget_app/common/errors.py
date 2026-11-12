"""화면 표현을 포함하지 않는 애플리케이션 오류."""


class AppError(Exception):
    def __init__(self, message: str, hint: str) -> None:
        super().__init__(message)
        self.hint = hint


class ValidationError(AppError):
    pass


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass


class StorageError(AppError):
    pass
