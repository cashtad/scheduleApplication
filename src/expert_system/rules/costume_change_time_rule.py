from .rule import ARule
from .violation import Violation
from graph import ScheduleGraph


class CostumeChangeTimeRule(ARule):
    """Rule: Sufficient time for costume change between Latin and Standard"""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        """Check for insufficient costume change time

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        competitors = graph.get_competitors()
        disciplines = self.config['disciplines']

        for competitor in competitors:
            performances = graph.get_performances_by_competition_ids(competitor.get_competition_ids())
            sorted(
                performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            for i in range(len(performances) - 1):
                curr = performances[i]
                next_perf = performances[i + 1]

                # Check for discipline change
                if (curr.competition and next_perf.competition and
                        curr.competition.discipline in disciplines and
                        next_perf.competition.discipline in disciplines and
                        curr.competition.discipline != next_perf.competition.discipline):

                    curr_end = self._ensure_datetime(curr.end_time)
                    next_start = self._ensure_datetime(next_perf.start_time)

                    gap_minutes = (next_start - curr_end).total_seconds() / 60
                    severity = self._get_severity(gap_minutes, reverse=True)

                    if severity:
                        threshold = self.config['thresholds'][severity.value]
                        shortage = threshold - gap_minutes
                        weight = self._calculate_weight(severity, shortage)

                        violations.append(Violation(
                            rule_name="CostumeChangeTime",
                            severity=severity,
                            weight=weight,
                            description=f"Nedostatečný čas ({gap_minutes:.0f} min) na převlečení kostýmu pro {competitor.full_name_1}",
                            entity_id=competitor.id,
                            entity_name=competitor.full_name_1,
                            details={
                                'gap_minutes': gap_minutes,
                                'required_minutes': self.config['min_gap_minutes'],
                                'shortage_minutes': shortage,
                                'from_discipline': curr.competition.discipline,
                                'to_discipline': next_perf.competition.discipline,
                                'from_time': curr_end,
                                'to_time': next_start
                            },
                            source_rows=self._source_rows(curr, next_perf),
                        ))

        return violations
