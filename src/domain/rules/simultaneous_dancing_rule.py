from __future__ import annotations

from src.domain import ScheduleRepository
from .simultaneous_rule import SimultaneousRule
from ..analysis import Violation

_DESCRIPTION = (
    "Tanečník {entity_name} má současně {count} vystoupení "
    "v čase {overlap_start}-{overlap_end}"
)


class SimultaneousDancingRule(SimultaneousRule):
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        if not self.enabled:
            return []

        violations: list[Violation] = []

        for competitor in repository.competitors:
            performances = self._get_sorted_performances(repository.list_assignments_of_human(competitor))
            if len(performances) < 2:
                continue

            entity_name = (
                f"{competitor.dancer_1_name}"
                + (f" {competitor.dancer_2_name}" if competitor.dancer_2_name else "")
            )

            violations.extend(
                self._check_overlaps_for_entity(
                    repository=repository,
                    performances=performances,
                    entity_id=entity_name,
                    entity_name=entity_name,
                    rule_name="SimultaneousDancing",
                    description_template=_DESCRIPTION,
                )
            )

        return violations