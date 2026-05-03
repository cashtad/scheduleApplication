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

    def dedup_key(self) -> tuple:
        context_items = tuple(sorted(self.context.items(), key=lambda x: x[0]))
        return self.code, self.severity.value, self.message, context_items


@dataclass(frozen=True, slots=True)
class ScheduleRepositoryValidationReport:
    errors: list[ScheduleRepositoryValidationIssue]
    warnings: list[ScheduleRepositoryValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    @property
    def total_issues(self) -> int:
        return len(self.errors) + len(self.warnings)
