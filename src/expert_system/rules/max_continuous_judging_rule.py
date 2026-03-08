from typing import Optional

from .rule import ARule
from .violation import Violation
from graph import ScheduleGraph


class MaxContinuousJudgingRule(ARule):
    """Rule: Judge should not judge too long without a break"""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        """Check for judges judging continuously for too long

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
            performances = sorted(
                graph.get_performances_of_jury(jury),
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            if not performances:
                continue

            continuous_duration = performances[0].duration
            block_performances = [performances[0]]

            for i in range(1, len(performances)):
                prev = performances[i - 1]
                curr = performances[i]

                prev_end = self._ensure_datetime(prev.end_time)
                curr_start = self._ensure_datetime(curr.start_time)

                gap = (curr_start - prev_end).total_seconds() / 60

                if gap < self.config['rest_time']:  # Consider continuous if gap < 10 minutes
                    continuous_duration += curr.duration
                    block_performances.append(curr)
                else:
                    violation = self._check_judging_duration(
                        jury, continuous_duration, block_performances
                    )
                    if violation:
                        violations.append(violation)

                    continuous_duration = curr.duration
                    block_performances = [curr]

            # Check last block
            violation = self._check_judging_duration(
                jury, continuous_duration, block_performances
            )
            if violation:
                violations.append(violation)

        return violations

    def _check_judging_duration(self, jury, duration, block_performances: list) -> Optional[Violation]:
        """Check if continuous judging duration exceeds thresholds

        Args:
            jury: Jury object
            duration: Duration of continuous judging
            block_performances: All performances in the continuous block

        Returns:
            Violation object if threshold exceeded, None otherwise
        """
        severity = self._get_severity(duration)

        if severity:
            threshold = self.config['thresholds'][severity.value]
            excess = duration - threshold
            weight = self._calculate_weight(severity, excess)
            start_perf = block_performances[0]
            end_perf = block_performances[-1]

            return Violation(
                rule_name="MaxContinuousJudging",
                severity=severity,
                weight=weight,
                description=f"Porotce {jury.fullname} porotuje {duration:.0f} minut bez přestávky",
                entity_id=jury.id,
                entity_name=jury.fullname,
                details={
                    'duration_minutes': duration,
                    'threshold_minutes': threshold,
                    'excess_minutes': excess,
                    'start_time': self._ensure_datetime(start_perf.start_time),
                    'end_time': self._ensure_datetime(end_perf.end_time)
                },
                source_rows=self._source_rows(*block_performances),
            )

        return None
