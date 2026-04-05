from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class MappingValidationError(Exception):
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass(frozen=True, slots=True)
class UserFacingParseError(Exception):
    code: str
    message: str
    column_key: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message
