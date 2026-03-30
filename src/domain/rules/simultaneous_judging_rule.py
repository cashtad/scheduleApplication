from __future__ import annotations

from ...domain import ScheduleRepository
from .simultaneous_rule import SimultaneousRule
from ..analysis import Violation

_DESCRIPTION = (
    "Porotce {entity_name} musí soudit současně {count} vystoupení "
    "v čase {overlap_start}-{overlap_end}"
)


class SimultaneousJudgingRule(SimultaneousRule):
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        if not self.enabled:
            return []

        violations: list[Violation] = []

        for jury_member in repository.jury_members:
            performances = self._get_sorted_performances(repository.list_assignments_of_human(jury_member))
            if len(performances) < 2:
                continue

            violations.extend(
                self._check_overlaps_for_entity(
                    repository=repository,
                    performances=performances,
                    entity_id=jury_member.fullname,
                    entity_name=jury_member.fullname,
                    rule_name="SimultaneousJudging",
                    description_template=_DESCRIPTION,
                )
            )

        return violations