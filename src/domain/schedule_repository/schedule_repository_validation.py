from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationIssueSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ScheduleRepositoryValidationIssue:
    code: str
    message: str
    severity: ValidationIssueSeverity
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScheduleRepositoryValidationReport:
    errors: list[ScheduleRepositoryValidationIssue]
    warnings: list[ScheduleRepositoryValidationIssue]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0