from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from graph import ScheduleGraph
from .severity import Severity
from .violation import Violation


class ARule(ABC):
    """Abstract base class for all schedule validation rules"""

    def __init__(self, config: dict):
        """Initialize rule with configuration

        Args:
            config: Rule-specific configuration from YAML
        """
        self.config = config
        self.enabled = config.get('enabled', True)

    @abstractmethod
    def check(self, graph: ScheduleGraph) -> list[Violation]:
        """Check rule against schedule graph

        Args:
            graph: Schedule graph to validate

        Returns:
            List of detected violations
        """
        pass

    @staticmethod
    def _source_rows(*performances) -> list[int]:
        """Collect source row indices from performance objects."""
        return [p.source_row for p in performances if p.source_row is not None]

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

    def _get_severity(self, value: float, reverse: bool = False) -> Optional[Severity]:
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
