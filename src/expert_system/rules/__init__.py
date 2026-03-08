from .costume_change_time_rule import CostumeChangeTimeRule
from .max_continuous_dancing_rule import MaxContinuousDancingRule
from .max_continuous_judging_rule import MaxContinuousJudgingRule
from .max_gap_between_performances_rule import MaxGapBetweenPerformancesRule
from .rule import ARule
from .severity import Severity
from .simultaneous_dancing_rule import SimultaneousDancingRule
from .simultaneous_judging_rule import SimultaneousJudgingRule
from .violation import Violation


def load_rules_from_config(config: dict) -> list[ARule]:
    """Load all rules from configuration dict

    Args:
        config: Already-loaded rules configuration dict (result of yaml.safe_load)

    Returns:
        List of initialized rule objects
    """
    rules = [
        MaxContinuousDancingRule(config['max_continuous_dancing']),
        CostumeChangeTimeRule(config['costume_change_time']),
        MaxContinuousJudgingRule(config['max_continuous_judging']),
        MaxGapBetweenPerformancesRule(config['max_gap_between_performances']),
        SimultaneousDancingRule(config['simultaneous_dancing']),
        SimultaneousJudgingRule(config['simultaneous_judging'])
    ]

    return rules


__all__ = [Severity, Violation, ARule, load_rules_from_config]
