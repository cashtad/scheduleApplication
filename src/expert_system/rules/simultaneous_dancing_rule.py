from .violation import Violation
from .simultaneous_rule import SimultaneousRule
from graph import ScheduleGraph

_DESCRIPTION = (
    "Tanečník {entity_name} má současně {count} vystoupení "
    "v čase {overlap_start}-{overlap_end}"
)


class SimultaneousDancingRule(SimultaneousRule):
    """Rule: Dancer cannot participate in multiple performances simultaneously."""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        if not self.enabled:
            return []

        violations = []
        for competitor in graph.get_competitors():
            performances = self._get_sorted_performances(
                graph.get_performances_of_competitor(competitor)
            )
            if len(performances) < 2:
                continue

            violations.extend(self._check_overlaps_for_entity(
                graph=graph,
                performances=performances,
                entity_id=competitor.full_name_1,
                entity_name=competitor.full_name_1,
                rule_name="SimultaneousDancing",
                description_template=_DESCRIPTION,
            ))

        return violations
