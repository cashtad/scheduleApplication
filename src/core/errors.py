from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppError(Exception):
    code: str
    user_message: str
    technical_message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.user_message}"


class InputValidationError(AppError):
    pass


class FileLoadError(AppError):
    pass


class MappingValidationError(AppError):
    pass


class RowParseError(AppError):
    pass


class AnalysisError(AppError):
    pass