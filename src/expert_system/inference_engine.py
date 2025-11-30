from dataclasses import dataclass
from pathlib import Path

import yaml

from src.expert_system.rules import Rule, Violation, Severity, load_rules_from_config


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


class InferenceEngine:
    """Inference engine for the expert system that validates schedule rules"""

    def __init__(self, rules_config_path: str):
        """Initialize inference engine with rules configuration

        Args:
            rules_config_path: Path to the rules configuration YAML file
        """
        self.rules_config_path = rules_config_path
        self.rules: list[Rule] = []
        self.general_config: dict = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        with open(self.rules_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.general_config = config.get('general', {})
        self.rules = load_rules_from_config(self.rules_config_path)

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

    def _group_by_severity(self, violations: list[Violation]) -> dict[Severity, list[Violation]]:
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

    def _group_by_rule(self, violations: list[Violation]) -> dict[str, list[Violation]]:
        """Group violations by rule name

        Args:
            violations: List of all violations

        Returns:
            Dictionary mapping rule name to list of violations
        """
        result = {}

        for violation in violations:
            if violation.rule_name not in result:
                result[violation.rule_name] = []
            result[violation.rule_name].append(violation)

        return result

    def _calculate_rating(self, total_weight: float) -> str:
        """Calculate schedule rating based on total violation weight

        Args:
            total_weight: Sum of weights from all violations

        Returns:
            Rating string in Czech
        """
        thresholds = self.general_config.get('schedule_rating', {})

        if total_weight <= thresholds.get('excellent', 0):
            return 'VYNIKAJÍCÍ'
        elif total_weight <= thresholds.get('good', 100):
            return 'DOBRÉ'
        elif total_weight <= thresholds.get('acceptable', 300):
            return 'PŘIJATELNÉ'
        elif total_weight <= thresholds.get('poor', 600):
            return 'ŠPATNÉ'
        else:
            return 'KRITICKÉ'
