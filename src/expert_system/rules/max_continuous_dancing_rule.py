from typing import Optional

from graph import ScheduleGraph
from .continuous_activity_rule import ContinuousActivityRule
from .violation import Violation


class MaxContinuousDancingRule(ContinuousActivityRule):
    """Rule: Dancer should not dance too long without a break."""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        if not self.enabled:
            return []

        violations = []
        for competitor in graph.get_competitors():
            performances = sorted(
                graph.get_performances_of_competitor(competitor),
                key=lambda p: self._ensure_datetime(p.start_time),
            )
            if len(performances) < 2:
                continue

            violations.extend(
                self._collect_violations_for_continuous_blocks(
                    performances,
                    check_block_fn=lambda dur, block, c=competitor: self._check_duration(c, dur, block),
                )
            )

        return violations

    def _check_duration(self, competitor, duration: float, block: list) -> Optional[Violation]:
        if competitor.count == 2:
            description = (
                f"Par {competitor.full_name_1} a {competitor.full_name_2}"
            )
        else:
            description = (
                f"Tanečník {competitor.full_name_1}"
            )
        description += f" tančí {int(duration)} minut bez přestávky"
        return self._build_duration_violation(
            duration=duration,
            block_performances=block,
            rule_name="MaxContinuousDancing",
            entity_id=competitor.full_name_1,
            entity_name=competitor.full_name_1,
            description=description,
        )