from dataclasses import dataclass

from .rules import Severity, Violation


@dataclass
class ScheduleAnalysisResult:
    """Result of schedule analysis containing violations and ratings"""
    total_weight: float
    rating: str
    violations: list[Violation]
    violations_by_severity: dict[Severity, list[Violation]]
    violations_by_rule: dict[str, list[Violation]]

    def get_summary(self) -> dict:
        """Get brief summary of analysis results

        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_weight': self.total_weight,
            'rating': self.rating,
            'total_violations': len(self.violations),
            'critical_count': len(self.violations_by_severity.get(Severity.CRITICAL, [])),
            'medium_count': len(self.violations_by_severity.get(Severity.MEDIUM, [])),
            'low_count': len(self.violations_by_severity.get(Severity.LOW, []))
        }
