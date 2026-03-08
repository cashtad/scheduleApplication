from .rule import ARule
from .violation import Violation
from graph import ScheduleGraph

class MaxGapBetweenPerformancesRule(ARule):
    """Rule: Dancer should not have too large gap between performances"""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        """Check for excessive gaps between performances

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        competitors = graph.get_competitors()

        for competitor in competitors:
            if len(competitor.performances) < 2:
                continue

            performances = sorted(
                competitor.performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            for i in range(len(performances) - 1):
                curr = performances[i]
                next_perf = performances[i + 1]

                curr_end = self._ensure_datetime(curr.end_time)
                next_start = self._ensure_datetime(next_perf.start_time)

                gap_minutes = (next_start - curr_end).total_seconds() / 60
                severity = self._get_severity(gap_minutes)

                if severity:
                    threshold = self.config['thresholds'][severity.value]
                    excess = gap_minutes - threshold
                    weight = self._calculate_weight(severity, excess)

                    violations.append(Violation(
                        rule_name="MaxGapBetweenPerformances",
                        severity=severity,
                        weight=weight,
                        description=f"Příliš velká přestávka ({gap_minutes:.0f} min) mezi vystoupeními pro {competitor.full_name_1}",
                        entity_id=competitor.id,
                        entity_name=competitor.full_name_1,
                        details={
                            'gap_minutes': gap_minutes,
                            'threshold_minutes': threshold,
                            'excess_minutes': excess,
                            'from_time': curr_end,
                            'to_time': next_start
                        },
                        source_rows=self._source_rows(curr, next_perf),
                    ))

        return violations
