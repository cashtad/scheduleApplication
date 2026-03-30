from __future__ import annotations

from ...infrastructure.config import RulesConfig
from .continuous_activity_rule import ContinuousActivityRule
from .costume_change_time_rule import CostumeChangeTimeRule
from .max_continuous_dancing_rule import MaxContinuousDancingRule
from .max_continuous_judging_rule import MaxContinuousJudgingRule
from .max_gap_between_performances_rule import MaxGapBetweenPerformancesRule
from .rule import ARule
from .simultaneous_dancing_rule import SimultaneousDancingRule
from .simultaneous_judging_rule import SimultaneousJudgingRule
from .simultaneous_rule import SimultaneousRule


def load_rules_from_config(config: RulesConfig) -> list[ARule]:
    return [
        MaxContinuousDancingRule(config.max_continuous_dancing),
        CostumeChangeTimeRule(config.costume_change_time),
        MaxContinuousJudgingRule(config.max_continuous_judging),
        MaxGapBetweenPerformancesRule(config.max_gap_between_performances),
        SimultaneousDancingRule(config.simultaneous_dancing),
        SimultaneousJudgingRule(config.simultaneous_judging),
    ]


__all__ = [
    "ARule",
    "ContinuousActivityRule",
    "SimultaneousRule",
    "load_rules_from_config",
]