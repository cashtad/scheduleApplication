from __future__ import annotations

from src.domain import ScheduleRepository
from .rule import ARule
from ..analysis import Violation


class CostumeChangeTimeRule(ARule):
    def check(self, repository: ScheduleRepository) -> list[Violation]:
        if not self.enabled:
            return []

        violations: list[Violation] = []
        disciplines = self.config.disciplines

        for competitor in repository.competitors:
            performances = repository.list_assignments_of_human(competitor)
            if len(performances) < 2:
                continue

            for curr, next_perf in zip(performances, performances[1:]):
                curr_comp = repository.find_competition_by_id(curr.competition_id)
                next_comp = repository.find_competition_by_id(next_perf.competition_id)

                if not curr_comp or not next_comp:
                    continue

                if (
                    curr_comp.discipline in disciplines
                    and next_comp.discipline in disciplines
                    and curr_comp.discipline != next_comp.discipline
                ):
                    curr_end = self._ensure_datetime(curr.end_time)
                    next_start = self._ensure_datetime(next_perf.start_time)

                    gap_minutes = (next_start - curr_end).total_seconds() / 60
                    severity = self._get_severity(gap_minutes, reverse=True)
                    if severity is None:
                        continue

                    threshold = self.config.thresholds.get(severity)
                    shortage = threshold - gap_minutes

                    entity_name = (
                        f"{competitor.dancer_1_name}"
                        + (f" a {competitor.dancer_2_name}" if competitor.dancer_2_name else "")
                    )

                    violations.append(
                        Violation(
                            rule_name="CostumeChangeTime",
                            severity=severity,
                            description=f"Nedostatečný čas ({gap_minutes:.0f} min) na převlečení kostýmu pro {competitor.dancer_1_name}",
                            entity_id=competitor.dancer_1_name,
                            entity_name=entity_name,
                            details={
                                "gap_minutes": gap_minutes,
                                "required_minutes": self.config.min_gap_minutes,
                                "shortage_minutes": shortage,
                                "from_discipline": curr_comp.discipline,
                                "to_discipline": next_comp.discipline,
                                "from_time": curr_end,
                                "to_time": next_start,
                            },
                            source_rows=self._source_rows(curr, next_perf),
                        )
                    )

        return violations