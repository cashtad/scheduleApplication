from __future__ import annotations

from abc import ABC
from datetime import datetime

from src.domain import Performance, ScheduleRepository
from .rule import ARule
from ..analysis import Severity, Violation


class SimultaneousRule(ARule, ABC):
    def _check_overlaps_for_entity(
        self,
        repository: ScheduleRepository,
        performances: list[Performance],
        entity_id: str,
        entity_name: str,
        rule_name: str,
        description_template: str,
    ) -> list[Violation]:
        violations: list[Violation] = []

        for i in range(len(performances)):
            for j in range(i + 1, len(performances)):
                perf1, perf2 = performances[i], performances[j]

                start1 = self._ensure_datetime(perf1.start_time)
                end1 = self._ensure_datetime(perf1.end_time)
                start2 = self._ensure_datetime(perf2.start_time)
                end2 = self._ensure_datetime(perf2.end_time)

                if not self._is_overlapping(start1, end1, start2, end2):
                    continue

                overlap_start = max(start1, start2)
                overlap_end = min(end1, end2)
                overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60

                comp1 = repository.find_competition_by_id(perf1.competition_id)
                comp2 = repository.find_competition_by_id(perf2.competition_id)

                description = description_template.format(
                    entity_name=entity_name,
                    overlap_start=overlap_start.strftime("%H:%M"),
                    overlap_end=overlap_end.strftime("%H:%M"),
                )

                violations.append(
                    Violation(
                        rule_name=rule_name,
                        severity=Severity.CRITICAL,
                        description=description,
                        entity_id=entity_id,
                        entity_name=entity_name,
                        details={
                            "overlap_minutes": overlap_minutes,
                            "overlap_start": overlap_start,
                            "overlap_end": overlap_end,
                            "competition1": comp1.name if comp1 else "neuvedeno",
                            "competition2": comp2.name if comp2 else "neuvedeno",
                        },
                        source_rows=self._source_rows(perf1, perf2),
                    )
                )

        return violations

    @staticmethod
    def _is_overlapping(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
        return start1 < end2 and start2 < end1

    def _get_sorted_performances(self, performances: list[Performance]) -> list[Performance]:
        return sorted(performances, key=lambda p: self._ensure_datetime(p.start_time))