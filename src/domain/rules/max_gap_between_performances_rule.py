from __future__ import annotations

from src.domain import ScheduleRepository
from .rule import ARule
from ..analysis import Violation


class MaxGapBetweenPerformancesRule(ARule):
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        if not self.enabled:
            return []

        violations: list[Violation] = []

        for competitor in repository.competitors:
            performances = repository.list_assignments_of_human(competitor)
            if len(performances) < 2:
                continue

            for curr, next_perf in zip(performances, performances[1:]):
                curr_end = self._ensure_datetime(curr.end_time)
                next_start = self._ensure_datetime(next_perf.start_time)

                gap_minutes = (next_start - curr_end).total_seconds() / 60
                severity = self._get_severity(gap_minutes)
                if severity is None:
                    continue

                threshold = self.config["thresholds"][severity.value]
                excess = gap_minutes - threshold

                entity_name = (
                    f"{competitor.dancer_1_name}"
                    + (f" a {competitor.dancer_2_name}" if competitor.dancer_2_name else "")
                )

                violations.append(
                    Violation(
                        rule_name="MaxGapBetweenPerformances",
                        severity=severity,
                        description=f"Příliš velká přestávka ({gap_minutes:.0f} min) mezi vystoupeními pro {competitor.dancer_1_name}",
                        entity_id=competitor.dancer_1_name,
                        entity_name=entity_name,
                        details={
                            "gap_minutes": gap_minutes,
                            "threshold_minutes": threshold,
                            "excess_minutes": excess,
                            "from_time": curr_end,
                            "to_time": next_start,
                        },
                        source_rows=self._source_rows(curr, next_perf),
                    )
                )

        return violations