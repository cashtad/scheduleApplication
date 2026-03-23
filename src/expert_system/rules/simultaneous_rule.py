from abc import ABC
from datetime import datetime

from graph import ScheduleGraph
from .rule import ARule
from .severity import Severity
from .violation import Violation


class SimultaneousRule(ARule, ABC):
    """Base class for rules that detect simultaneous overlapping performances."""

    def _check_overlaps_for_entity(
        self,
        graph: ScheduleGraph,
        performances: list,
        entity_id: str,
        entity_name: str,
        rule_name: str,
        description_template: str,
    ) -> list[Violation]:
        """Check all pairs of performances for time overlap and return violations.

        Args:
            graph: Schedule graph
            performances: Sorted list of performances for one entity
            entity_id: Identifier of the entity (competitor name or jury id)
            entity_name: Display name of the entity
            rule_name: Name of the rule being checked
            description_template: f-string template; receives {entity_name}, {count},
                                   {overlap_start}, {overlap_end} as keyword args
        """
        violations = []

        for i in range(len(performances)):
            for j in range(i + 1, len(performances)):
                perf1, perf2 = performances[i], performances[j]

                start1 = self._ensure_datetime(perf1.start_time)
                end1   = self._ensure_datetime(perf1.end_time)
                start2 = self._ensure_datetime(perf2.start_time)
                end2   = self._ensure_datetime(perf2.end_time)

                if not self._is_overlapping(start1, end1, start2, end2):
                    continue

                overlap_start   = max(start1, start2)
                overlap_end     = min(end1, end2)
                overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60
                weight          = self.config["weights"]["base_critical"]

                comp1 = graph.get_competition_by_id(perf1.competition_id)
                comp2 = graph.get_competition_by_id(perf2.competition_id)

                overlapping_count = sum(
                    1 for p in performances
                    if self._is_overlapping(
                        start1, end1,
                        self._ensure_datetime(p.start_time),
                        self._ensure_datetime(p.end_time),
                    )
                )
                description = description_template.format(
                    entity_name=entity_name,
                    count=overlapping_count,
                    overlap_start=overlap_start.strftime("%H:%M"),
                    overlap_end=overlap_end.strftime("%H:%M"),
                )

                violations.append(Violation(
                    rule_name=rule_name,
                    severity=Severity.CRITICAL,
                    weight=weight,
                    description=description,
                    entity_id=entity_id,
                    entity_name=f"{entity_name}",
                    details={
                        "overlap_minutes":    overlap_minutes,
                        "performance1_start": start1,
                        "performance1_end":   end1,
                        "performance2_start": start2,
                        "performance2_end":   end2,
                        "overlap_start":      overlap_start,
                        "overlap_end":        overlap_end,
                        "competition1":       comp1.name if comp1 else "N/A",
                        "competition2":       comp2.name if comp2 else "N/A",
                    },
                    source_rows=self._source_rows(perf1, perf2),
                ))

        return violations

    @staticmethod
    def _is_overlapping(
        start1: datetime, end1: datetime,
        start2: datetime, end2: datetime,
    ) -> bool:
        """Check if two time intervals overlap

        Args:
            start1: Start time of first interval
            end1: End time of first interval
            start2: Start time of second interval
            end2: End time of second interval

        Returns:
            True if intervals overlap, False otherwise
        """
        return start1 < end2 and start2 < end1

    def _get_sorted_performances(self, performances) -> list:
        """Return performances sorted by start time."""
        return sorted(performances, key=lambda p: self._ensure_datetime(p.start_time))