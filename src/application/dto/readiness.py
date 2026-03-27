from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReadinessDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"

class ReadinessReasonSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ReadinessReason:
    code: str
    severity: ReadinessReasonSeverity  # "error" | "warning"
    message_en: str
    message_cz: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalyzeReadinessResult:
    decision: ReadinessDecision
    reasons: list[ReadinessReason]

    @property
    def is_allowed(self) -> bool:
        return self.decision == ReadinessDecision.ALLOW