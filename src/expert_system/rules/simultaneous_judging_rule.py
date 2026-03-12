from graph import ScheduleGraph
from .simultaneous_rule import SimultaneousRule
from .violation import Violation

_DESCRIPTION = (
    "Porotce {entity_name} musí soudit současně {count} vystoupení "
    "v čase {overlap_start}-{overlap_end}"
)


class SimultaneousJudgingRule(SimultaneousRule):
    """Rule: Judge cannot judge multiple performances simultaneously."""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        if not self.enabled:
            return []

        violations = []
        for jury in graph.get_juries():
            performances = self._get_sorted_performances(
                graph.get_performances_of_jury(jury)
            )
            if len(performances) < 2:
                continue

            violations.extend(self._check_overlaps_for_entity(
                graph=graph,
                performances=performances,
                entity_id=jury.fullname,
                entity_name=jury.fullname,
                rule_name="SimultaneousJudging",
                description_template=_DESCRIPTION,
            ))

        return violations