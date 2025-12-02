from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import yaml


class Severity(Enum):
    """Severity level of rule violation"""
    CRITICAL = "critical"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Violation:
    """Rule violation with all relevant information"""
    rule_name: str  # Name of the violated rule
    severity: Severity  # Severity level
    weight: float  # Calculated weight of violation
    description: str  # Human-readable description
    entity_id: str  # ID of dancer/judge involved
    entity_name: str  # Name of dancer/judge
    details: dict[str, Any]  # Additional details about the violation


class Rule(ABC):
    """Abstract base class for all schedule validation rules"""

    def __init__(self, config: dict):
        """Initialize rule with configuration

        Args:
            config: Rule-specific configuration from YAML
        """
        self.config = config
        self.enabled = config.get('enabled', True)

    @abstractmethod
    def check(self, graph) -> list[Violation]:
        """Check rule against schedule graph

        Args:
            graph: Schedule graph to validate

        Returns:
            List of detected violations
        """
        pass

    def _calculate_weight(self, severity: Severity, excess: float = 0) -> float:
        """Calculate violation weight based on severity and excess

        Args:
            severity: Severity level of the violation
            excess: Amount exceeding the threshold (in minutes)

        Returns:
            Calculated weight value
        """
        weights = self.config['weights']
        base_weight = weights[f'base_{severity.value}']
        coefficient = weights.get('coefficient_per_minute', 0)
        return base_weight + (excess * coefficient)

    def _get_severity(self, value: float, reverse: bool = False) -> Severity | None:
        """Determine severity level based on threshold comparison

        Args:
            value: Value to check against thresholds
            reverse: If True, lower values are worse (e.g., costume change time)

        Returns:
            Severity level or None if within acceptable range
        """
        value = int(value)

        thresholds = self.config['thresholds']

        if reverse:
            # For reverse checks (e.g., minimum required time)
            if value <= thresholds['critical']:
                return Severity.CRITICAL
            elif value <= thresholds['medium']:
                return Severity.MEDIUM
            elif value <= thresholds['low']:
                return Severity.LOW
        else:
            # For normal checks (e.g., maximum allowed time)
            if value >= thresholds['critical']:
                return Severity.CRITICAL
            elif value >= thresholds['medium']:
                return Severity.MEDIUM
            elif value >= thresholds['low']:
                return Severity.LOW

        return None

    @staticmethod
    def _ensure_datetime(dt) -> datetime:
        """Convert string to datetime if necessary

        Args:
            dt: Datetime object or string to convert

        Returns:
            Datetime object

        Raises:
            ValueError: If string cannot be parsed
            TypeError: If type is not supported
        """
        if isinstance(dt, datetime):
            return dt
        if isinstance(dt, str):
            # Try parsing different time formats
            for fmt in ['%H:%M:%S', '%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']:
                try:
                    return datetime.strptime(dt, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Nelze parsovat čas: {dt}")
        raise TypeError(f"Nepodporovaný typ pro čas: {type(dt)}")


class MaxContinuousDancingRule(Rule):
    """Rule: Dancer should not dance too long without a break"""

    def check(self, graph) -> list[Violation]:
        """Check for dancers dancing continuously for too long

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        competitors = graph.get_competitors()

        for competitor in competitors:
            # Sort performances by start time
            performances = sorted(
                competitor.performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            if len(performances) < 2:
                continue

            # Find continuous blocks of performances
            continuous_duration = performances[0].duration
            block_start = performances[0]

            for i in range(1, len(performances)):
                prev = performances[i - 1]
                curr = performances[i]

                prev_start = self._ensure_datetime(prev.start_time)
                prev_end = self._ensure_datetime(prev.end_time)
                curr_start = self._ensure_datetime(curr.start_time)
                curr_end = self._ensure_datetime(curr.end_time)

                # If gap is less than 12 minutes, consider it continuous
                gap = (curr_start - prev_end).total_seconds() / 60

                if gap < 10:  # TODO: Move constant to config file
                    continuous_duration += curr.duration
                else:
                    # Check completed block
                    violation = self._check_duration(
                        competitor, continuous_duration, block_start, prev
                    )
                    if violation:
                        violations.append(violation)

                    # Start new block
                    continuous_duration = curr.duration
                    block_start = curr

            # Check last block
            violation = self._check_duration(
                competitor, continuous_duration, block_start, performances[-1]
            )
            if violation:
                violations.append(violation)

        return violations

    def _check_duration(self, competitor, duration, start_perf, end_perf) -> Violation | None:
        """Check if continuous duration exceeds thresholds

        Args:
            competitor: Competitor object
            duration: Duration of continuous dancing
            start_perf: First performance in the block
            end_perf: Last performance in the block

        Returns:
            Violation object if threshold exceeded, None otherwise
        """
        severity = self._get_severity(duration)
        duration = int(duration)

        if severity:
            threshold = self.config['thresholds'][severity.value]
            excess = duration - threshold
            weight = self._calculate_weight(severity, excess)

            return Violation(
                rule_name="MaxContinuousDancing",
                severity=severity,
                weight=weight,
                description=f"Tanečník {competitor.full_name_1} tančí {duration:.0f} minut bez přestávky",
                entity_id=competitor.id,
                entity_name=competitor.full_name_1,
                details={
                    'duration_minutes': duration,
                    'threshold_minutes': threshold,
                    'excess_minutes': excess,
                    'start_time': self._ensure_datetime(start_perf.start_time),
                    'end_time': self._ensure_datetime(end_perf.end_time)
                }
            )

        return None


class CostumeChangeTimeRule(Rule):
    """Rule: Sufficient time for costume change between Latin and Standard"""

    def check(self, graph) -> list[Violation]:
        """Check for insufficient costume change time

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        competitors = graph.get_competitors()
        disciplines = self.config['disciplines']

        for competitor in competitors:
            performances = sorted(
                competitor.performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            for i in range(len(performances) - 1):
                curr = performances[i]
                next_perf = performances[i + 1]

                # Check for discipline change
                if (curr.competition and next_perf.competition and
                    curr.competition.discipline in disciplines and
                    next_perf.competition.discipline in disciplines and
                    curr.competition.discipline != next_perf.competition.discipline):

                    curr_end = self._ensure_datetime(curr.end_time)
                    next_start = self._ensure_datetime(next_perf.start_time)

                    gap_minutes = (next_start - curr_end).total_seconds() / 60
                    severity = self._get_severity(gap_minutes, reverse=True)

                    if severity:
                        threshold = self.config['thresholds'][severity.value]
                        shortage = threshold - gap_minutes
                        weight = self._calculate_weight(severity, shortage)

                        violations.append(Violation(
                            rule_name="CostumeChangeTime",
                            severity=severity,
                            weight=weight,
                            description=f"Nedostatečný čas ({gap_minutes:.0f} min) na převlečení kostýmu pro {competitor.full_name_1}",
                            entity_id=competitor.id,
                            entity_name=competitor.full_name_1,
                            details={
                                'gap_minutes': gap_minutes,
                                'required_minutes': self.config['min_gap_minutes'],
                                'shortage_minutes': shortage,
                                'from_discipline': curr.competition.discipline,
                                'to_discipline': next_perf.competition.discipline,
                                'from_time': curr_end,
                                'to_time': next_start
                            }
                        ))

        return violations


class MaxContinuousJudgingRule(Rule):
    """Rule: Judge should not judge too long without a break"""

    def check(self, graph) -> list[Violation]:
        """Check for judges judging continuously for too long

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        juries = graph.get_juries()

        for jury in juries:
            if not jury.performances:
                continue

            performances = sorted(
                jury.performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            # Track continuous judging blocks
            continuous_duration = performances[0].duration
            block_start = performances[0]

            for i in range(1, len(performances)):
                prev = performances[i - 1]
                curr = performances[i]

                prev_end = self._ensure_datetime(prev.end_time)
                curr_start = self._ensure_datetime(curr.start_time)

                gap = (curr_start - prev_end).total_seconds() / 60

                if gap < 10:  # Consider continuous if gap < 10 minutes
                    continuous_duration += curr.duration
                else:
                    violation = self._check_judging_duration(
                        jury, continuous_duration, block_start, prev
                    )
                    if violation:
                        violations.append(violation)

                    continuous_duration = curr.duration
                    block_start = curr

            # Check last block
            violation = self._check_judging_duration(
                jury, continuous_duration, block_start, performances[-1]
            )
            if violation:
                violations.append(violation)

        return violations

    def _check_judging_duration(self, jury, duration, start_perf, end_perf) -> Violation | None:
        """Check if continuous judging duration exceeds thresholds

        Args:
            jury: Jury object
            duration: Duration of continuous judging
            start_perf: First performance in the block
            end_perf: Last performance in the block

        Returns:
            Violation object if threshold exceeded, None otherwise
        """
        severity = self._get_severity(duration)

        if severity:
            threshold = self.config['thresholds'][severity.value]
            excess = duration - threshold
            weight = self._calculate_weight(severity, excess)

            return Violation(
                rule_name="MaxContinuousJudging",
                severity=severity,
                weight=weight,
                description=f"Porotce {jury.name} porotuje {duration:.0f} minut bez přestávky",
                entity_id=jury.id,
                entity_name=jury.name,
                details={
                    'duration_minutes': duration,
                    'threshold_minutes': threshold,
                    'excess_minutes': excess,
                    'start_time': self._ensure_datetime(start_perf.start_time),
                    'end_time': self._ensure_datetime(end_perf.end_time)
                }
            )

        return None


class MaxGapBetweenPerformancesRule(Rule):
    """Rule: Dancer should not have too large gap between performances"""

    def check(self, graph) -> list[Violation]:
        """Check for excessive gaps between performances

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        competitors = graph.get_competitors()

        for competitor in competitors:
            if len(competitor.performances) < 2:
                continue

            performances = sorted(
                competitor.performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            for i in range(len(performances) - 1):
                curr = performances[i]
                next_perf = performances[i + 1]

                curr_end = self._ensure_datetime(curr.end_time)
                next_start = self._ensure_datetime(next_perf.start_time)

                gap_minutes = (next_start - curr_end).total_seconds() / 60
                severity = self._get_severity(gap_minutes)

                if severity:
                    threshold = self.config['thresholds'][severity.value]
                    excess = gap_minutes - threshold
                    weight = self._calculate_weight(severity, excess)

                    violations.append(Violation(
                        rule_name="MaxGapBetweenPerformances",
                        severity=severity,
                        weight=weight,
                        description=f"Příliš velká přestávka ({gap_minutes:.0f} min) mezi vystoupeními pro {competitor.full_name_1}",
                        entity_id=competitor.id,
                        entity_name=competitor.full_name_1,
                        details={
                            'gap_minutes': gap_minutes,
                            'threshold_minutes': threshold,
                            'excess_minutes': excess,
                            'first_performance_end': curr_end,
                            'second_performance_start': next_start
                        }
                    ))

        return violations


def load_rules_from_config(config_path: str) -> list[Rule]:
    """Load all rules from configuration file

    Args:
        config_path: Path to rules configuration YAML file

    Returns:
        List of initialized rule objects
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    rules = [
        MaxContinuousDancingRule(config['max_continuous_dancing']),
        CostumeChangeTimeRule(config['costume_change_time']),
        MaxContinuousJudgingRule(config['max_continuous_judging']),
        MaxGapBetweenPerformancesRule(config['max_gap_between_performances'])
    ]

    return rules
