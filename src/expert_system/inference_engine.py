from collections import defaultdict

from .rules import Severity, Violation, load_rules_from_config
from .schedule_analysis_result import ScheduleAnalysisResult


class InferenceEngine:
    """Expert-system inference engine that validates schedule rules."""

    def __init__(self, rules_config: dict):
        """Initialize inference engine with rules configuration

        Args:
            rules_config: Already-loaded rules configuration dict (result of yaml.safe_load)
        """
        self.general_config = rules_config.get("general", {})
        self.rules = load_rules_from_config(rules_config)

    def analyze_schedule(self, graph) -> ScheduleAnalysisResult:
        """Analyze schedule for rule violations

        Args:
            graph: Schedule graph object (ScheduleGraph)

        Returns:
            ScheduleAnalysisResult with all detected violations and ratings
        """
        all_violations = []

        # Check all rules against the graph
        for rule in self.rules:
            violations = rule.check(graph)
            all_violations.extend(violations)

        # Group violations by different criteria
        violations_by_severity = self._group_by_severity(all_violations)
        violations_by_rule = self._group_by_rule(all_violations)

        # Calculate total weight of all violations
        total_weight = sum(v.weight for v in all_violations)

        # Determine overall rating
        rating = self._calculate_rating(total_weight)

        return ScheduleAnalysisResult(
            total_weight=total_weight,
            rating=rating,
            violations=all_violations,
            violations_by_severity=violations_by_severity,
            violations_by_rule=violations_by_rule
        )

    @staticmethod
    def _group_by_severity(violations: list[Violation]) -> dict[Severity, list[Violation]]:
        """Group violations by severity level

        Args:
            violations: List of all violations

        Returns:
            Dictionary mapping severity to list of violations
        """
        result = {severity: [] for severity in Severity}

        for violation in violations:
            result[violation.severity].append(violation)
        return result

    @staticmethod
    def _group_by_rule(violations: list[Violation]) -> dict[str, list[Violation]]:
        """Group violations by rule name."""
        result: dict[str, list[Violation]] = defaultdict(list)
        for violation in violations:
            result[violation.rule_name].append(violation)
        return dict(result)

    def _calculate_rating(self, total_weight: float) -> str:
        """Map total violation weight to a Czech rating label."""
        thresholds = self.general_config.get("schedule_rating", {})
        if total_weight <= thresholds.get("excellent",   0):   return "VYNIKAJÍCÍ"
        if total_weight <= thresholds.get("good",      100):   return "DOBRÉ"
        if total_weight <= thresholds.get("acceptable", 300):   return "PŘIJATELNÉ"
        if total_weight <= thresholds.get("poor",       600):   return "ŠPATNÉ"
        return "KRITICKÉ"