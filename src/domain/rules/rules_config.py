from __future__ import annotations

from dataclasses import dataclass
from ..analysis import Severity


@dataclass(frozen=True, slots=True)
class RuleConfig:
    enabled: bool
    thresholds: dict[Severity, int] | None = None
    rest_time: int | None = None
    disciplines: tuple[str, ...] | None = None
    min_gap_minutes: int | None = None


@dataclass(frozen=True, slots=True)
class RulesConfig:
    max_continuous_dancing: RuleConfig
    costume_change_time: RuleConfig
    max_continuous_judging: RuleConfig
    max_gap_between_performances: RuleConfig
    simultaneous_dancing: RuleConfig
    simultaneous_judging: RuleConfig
