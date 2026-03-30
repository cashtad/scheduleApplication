from __future__ import annotations

from collections import defaultdict

from ..rules import load_rules_from_config
from ...domain import ScheduleRepository
from .schedule_analysis_result import ScheduleAnalysisResult
from .severity import Severity
from .violation import Violation


class InferenceEngine:
    def __init__(self, rules_config: dict) -> None:
        self.general_config = rules_config.get("general", {})
        self.rules = load_rules_from_config(rules_config)

    def analyze(self, repository: ScheduleRepository) -> ScheduleAnalysisResult:
        all_violations: list[Violation] = []

        for rule in self.rules:
            all_violations.extend(rule.check(repository))

        all_violations = self._deduplicate_violations(all_violations)
        violations_by_severity = self._group_by_severity(all_violations)
        violations_by_rule = self._group_by_rule(all_violations)
        total_weight = sum(v.weight for v in all_violations)
        rating = self._calculate_rating(total_weight)

        return ScheduleAnalysisResult(
            total_weight=total_weight,
            rating=rating,
            violations=all_violations,
            violations_by_severity=violations_by_severity,
            violations_by_rule=violations_by_rule,
        )

    @staticmethod
    def _group_by_severity(violations: list[Violation]) -> dict[Severity, list[Violation]]:
        result = {severity: [] for severity in Severity}
        for violation in violations:
            result[violation.severity].append(violation)
        return result

    @staticmethod
    def _group_by_rule(violations: list[Violation]) -> dict[str, list[Violation]]:
        grouped: dict[str, list[Violation]] = defaultdict(list)
        for violation in violations:
            grouped[violation.rule_name].append(violation)
        return dict(grouped)

    @staticmethod
    def _deduplicate_violations(violations: list[Violation]) -> list[Violation]:
        unique: dict[tuple, Violation] = {}
        for v in violations:
            unique[v.dedup_key()] = v
        return list(unique.values())

    def _calculate_rating(self, total_weight: float) -> str:
        thresholds = self.general_config.get("schedule_rating", {})
        if total_weight <= thresholds.get("excellent", 0):
            return "VYNIKAJÍCÍ"
        if total_weight <= thresholds.get("good", 1000):
            return "DOBRÉ"
        if total_weight <= thresholds.get("acceptable", 2000):
            return "PŘIJATELNÉ"
        if total_weight <= thresholds.get("poor", 3000):
            return "ŠPATNÉ"
        return "KRITICKÉ"