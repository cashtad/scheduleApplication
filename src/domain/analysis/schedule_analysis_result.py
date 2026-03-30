from __future__ import annotations

from dataclasses import dataclass

from .severity import Severity
from .violation import Violation


@dataclass(frozen=True, slots=True)
class ScheduleAnalysisResult:
    total_weight: float
    rating: str
    violations: list[Violation]
    violations_by_severity: dict[Severity, list[Violation]]
    violations_by_rule: dict[str, list[Violation]]

    def get_summary(self) -> dict[str, int | float | str]:
        return {
            "total_weight": self.total_weight,
            "rating": self.rating,
            "total_violations": len(self.violations),
            "critical_count": len(self.violations_by_severity.get(Severity.CRITICAL, [])),
            "medium_count": len(self.violations_by_severity.get(Severity.MEDIUM, [])),
            "low_count": len(self.violations_by_severity.get(Severity.LOW, [])),
        }