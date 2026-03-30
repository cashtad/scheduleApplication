from __future__ import annotations

from collections import defaultdict

from .schedule_analysis_result import ScheduleAnalysisResult
from .severity import Severity
from .violation import Violation
from ..rules import load_rules_from_config
from ...domain import ScheduleRepository


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

        return ScheduleAnalysisResult(
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
        for violation in violations:
            unique[violation.dedup_key()] = violation
        return list(unique.values())
