from __future__ import annotations

from ...domain import ScheduleRepository
from .continuous_activity_rule import ContinuousActivityRule
from ..analysis import Violation


class MaxContinuousDancingRule(ContinuousActivityRule):
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        if not self.enabled:
            return []

        violations: list[Violation] = []
        for competitor in repository.competitors:
            performances = repository.list_assignments_of_human(competitor)
            if len(performances) < 2:
                continue

            violations.extend(
                self._collect_violations_for_continuous_blocks(
                    performances=performances,
                    check_block_fn=lambda dur, block, c=competitor: self._check_duration(c, dur, block),
                )
            )
        return violations

    def _check_duration(self, competitor, duration: float, block: list) -> Violation | None:
        if competitor.participants_per_entry == 2:
            who = f"Pár {competitor.dancer_1_name} a {competitor.dancer_2_name}"
        else:
            who = f"Tanečník {competitor.dancer_1_name}"

        description = f"{who} tančí {int(duration)} minut bez přestávky"
        entity_name = (
            f"{competitor.dancer_1_name}"
            + (f" a {competitor.dancer_2_name}" if competitor.dancer_2_name else "")
        )

        return self._build_duration_violation(
            duration=duration,
            block_performances=block,
            rule_name="MaxContinuousDancing",
            entity_id=competitor.dancer_1_name,
            entity_name=entity_name,
            description=description,
        )