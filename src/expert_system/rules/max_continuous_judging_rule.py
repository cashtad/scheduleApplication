from typing import Optional

from graph import ScheduleGraph
from .continuous_activity_rule import ContinuousActivityRule
from .violation import Violation


class MaxContinuousJudgingRule(ContinuousActivityRule):
    """Rule: Judge should not judge too long without a break."""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        if not self.enabled:
            return []

        violations = []
        for jury in graph.get_juries():
            performances = sorted(
                graph.get_performances_of_jury(jury),
                key=lambda p: self._ensure_datetime(p.start_time),
            )
            violations.extend(
                self._collect_violations_for_continuous_blocks(
                    performances,
                    check_block_fn=lambda dur, block, j=jury: self._check_duration(j, dur, block),
                )
            )

        return violations

    def _check_duration(self, jury, duration: float, block: list) -> Optional[Violation]:
        description = (
            f"Porotce {jury.fullname} porotuje {int(duration)} minut bez přestávky"
        )
        return self._build_duration_violation(
            duration=duration,
            block_performances=block,
            rule_name="MaxContinuousJudging",
            entity_id=jury.fullname,
            entity_name=jury.fullname,
            description=description,
        )