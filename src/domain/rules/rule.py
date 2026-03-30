from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ...domain import ScheduleRepository
from ..analysis import Severity
from ..analysis import Violation


class ARule(ABC):
    def __init__(self, config: dict) -> None:
        self.config = config
        self.enabled = bool(config.get("enabled", True))

    @abstractmethod
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        raise NotImplementedError

    @staticmethod
    def _source_rows(*performances) -> list[int]:
        return [p.source_row for p in performances if p.source_row is not None]

    def _calculate_weight(self, severity: Severity, excess: float = 0) -> float:
        weights = self.config["weights"]
        base_weight = float(weights[f"base_{severity.value}"])
        coefficient = float(weights.get("coefficient_per_minute", 0))
        return base_weight + (float(excess) * coefficient)

    def _get_severity(self, value: float, reverse: bool = False) -> Severity | None:
        value_i = int(value)
        thresholds = self.config["thresholds"]

        if reverse:
            if value_i <= thresholds["critical"]:
                return Severity.CRITICAL
            if value_i <= thresholds["medium"]:
                return Severity.MEDIUM
            if value_i <= thresholds["low"]:
                return Severity.LOW
            return None

        if value_i >= thresholds["critical"]:
            return Severity.CRITICAL
        if value_i >= thresholds["medium"]:
            return Severity.MEDIUM
        if value_i >= thresholds["low"]:
            return Severity.LOW
        return None

    @staticmethod
    def _ensure_datetime(dt) -> datetime:
        if isinstance(dt, datetime):
            return dt
        if isinstance(dt, str):
            for fmt in ("%H:%M:%S", "%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.strptime(dt, fmt)
                except ValueError:
                    pass
            raise ValueError(f"Cannot parse datetime: {dt}")
        raise TypeError(f"Unsupported datetime type: {type(dt)}")