from __future__ import annotations

from src.domain import ScheduleRepository
from .continuous_activity_rule import ContinuousActivityRule
from ..analysis import Violation


class MaxContinuousJudgingRule(ContinuousActivityRule):
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        if not self.enabled:
            return []

        violations: list[Violation] = []
        for jury_member in repository.jury_members:
            performances = repository.list_assignments_of_human(jury_member)
            if len(performances) < 2:
                continue

            violations.extend(
                self._collect_violations_for_continuous_blocks(
                    performances=performances,
                    check_block_fn=lambda dur, block, j=jury_member: self._check_duration(j, dur, block),
                )
            )
        return violations

    def _check_duration(self, jury_member, duration: float, block: list) -> Violation | None:
        description = f"Porotce {jury_member.fullname} porotuje {int(duration)} minut bez přestávky"

        return self._build_duration_violation(
            duration=duration,
            block_performances=block,
            rule_name="MaxContinuousJudging",
            entity_id=jury_member.fullname,
            entity_name=jury_member.fullname,
            description=description,
        )