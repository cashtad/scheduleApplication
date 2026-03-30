from __future__ import annotations

from collections import defaultdict

from src.domain import ScheduleRepository
from src.infrastructure.config import RulesConfig
from ..rules import load_rules_from_config
from .schedule_analysis_result import ScheduleAnalysisResult
from .severity import Severity
from .violation import Violation


class InferenceEngine:
    def __init__(self, rules_config: RulesConfig) -> None:
        self.rules = load_rules_from_config(rules_config)

    def analyze(self, repository: ScheduleRepository) -> ScheduleAnalysisResult:
        violations: list[Violation] = []

        for rule in self.rules:
            violations.extend(rule.check(repository))

        deduped = self._deduplicate_violations(violations)
        by_severity = self._group_by_severity(deduped)
        by_rule = self._group_by_rule(deduped)

        return ScheduleAnalysisResult(
            violations=deduped,
            violations_by_severity=by_severity,
            violations_by_rule=by_rule,
        )

    @staticmethod
    def _group_by_severity(violations: list[Violation]) -> dict[Severity, list[Violation]]:
        grouped: dict[Severity, list[Violation]] = {severity: [] for severity in Severity}
        for violation in violations:
            grouped[violation.severity].append(violation)
        return grouped

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