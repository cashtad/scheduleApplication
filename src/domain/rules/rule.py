from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ...domain import ScheduleRepository
from ..analysis import Severity, Violation
from ...infrastructure.config import RuleConfig


class ARule(ABC):
    def __init__(self, config: RuleConfig) -> None:
        self.config = config
        self.enabled = config.enabled

    @abstractmethod
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        raise NotImplementedError

    @staticmethod
    def _source_rows(*performances) -> list[int]:
        return [p.source_row for p in performances if p.source_row is not None]

    def _get_severity(self, value: float, reverse: bool = False) -> Severity | None:
        if self.config.thresholds is None:
            return None

        value_i = int(value)
        thresholds = self.config.thresholds

        if reverse:
            if value_i <= thresholds.critical:
                return Severity.CRITICAL
            if value_i <= thresholds.medium:
                return Severity.MEDIUM
            if value_i <= thresholds.low:
                return Severity.LOW
            return None

        if value_i >= thresholds.critical:
            return Severity.CRITICAL
        if value_i >= thresholds.medium:
            return Severity.MEDIUM
        if value_i >= thresholds.low:
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