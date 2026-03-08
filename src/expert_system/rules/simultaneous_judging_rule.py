from datetime import datetime

from .rule import ARule
from .severity import Severity
from .violation import Violation
from graph import ScheduleGraph


class SimultaneousJudgingRule(ARule):
    """Rule: Judge cannot judge multiple performances simultaneously"""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        """Check for judges scheduled to judge overlapping performances

        Args:
            graph: Schedule graph

        Returns:
            List of violations found
        """
        violations = []

        if not self.enabled:
            return violations

        juries = graph.get_juries()

        for jury in juries:
            if len(jury.performances) < 2:
                continue

            performances = sorted(
                jury.performances,
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            # Check each pair of performances for time overlap
            for i in range(len(performances)):
                for j in range(i + 1, len(performances)):
                    perf1 = performances[i]
                    perf2 = performances[j]

                    start1 = self._ensure_datetime(perf1.start_time)
                    end1 = self._ensure_datetime(perf1.end_time)
                    start2 = self._ensure_datetime(perf2.start_time)
                    end2 = self._ensure_datetime(perf2.end_time)

                    # Check if performances overlap
                    if self._is_overlapping(start1, end1, start2, end2):
                        weight = self.config['weights']['base_critical']

                        overlap_start = max(start1, start2)
                        overlap_end = min(end1, end2)
                        overlap_minutes = (overlap_end - overlap_start).total_seconds() / 60

                        violations.append(Violation(
                            rule_name="SimultaneousJudging",
                            severity=Severity.CRITICAL,
                            weight=weight,
                            description=f"Porotce {jury.name} musí soudit současně {len([p for p in performances if self._is_overlapping(start1, end1, self._ensure_datetime(p.start_time), self._ensure_datetime(p.end_time))])} vystoupení v čase {overlap_start.strftime('%H:%M')}-{overlap_end.strftime('%H:%M')}",
                            entity_id=jury.id,
                            entity_name=jury.name,
                            details={
                                'overlap_minutes': overlap_minutes,
                                'performance1_start': start1,
                                'performance1_end': end1,
                                'performance2_start': start2,
                                'performance2_end': end2,
                                'overlap_start': overlap_start,
                                'overlap_end': overlap_end,
                                'competition1': perf1.competition.name if perf1.competition else 'N/A',
                                'competition2': perf2.competition.name if perf2.competition else 'N/A'
                            },
                            source_rows=self._source_rows(perf1, perf2),
                        ))

        return violations

    @staticmethod
    def _is_overlapping(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
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
