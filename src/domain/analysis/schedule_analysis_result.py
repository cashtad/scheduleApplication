from __future__ import annotations

from dataclasses import dataclass

from .severity import Severity
from .violation import Violation


@dataclass(frozen=True, slots=True)
class ScheduleAnalysisResult:
    violations: list[Violation]
    violations_by_severity: dict[Severity, list[Violation]]
    violations_by_rule: dict[str, list[Violation]]

    @property
    def total_violations(self) -> int:
        return len(self.violations)

    def get_summary(self) -> dict[str, int | str]:
        return {
            "total_violations": self.total_violations,
            "critical_count": len(self.violations_by_severity.get(Severity.CRITICAL, [])),
            "medium_count": len(self.violations_by_severity.get(Severity.MEDIUM, [])),
            "low_count": len(self.violations_by_severity.get(Severity.LOW, [])),
        }