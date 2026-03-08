from typing import Optional

from .rule import ARule
from .violation import Violation
from graph import ScheduleGraph


class MaxContinuousDancingRule(ARule):
    """Rule: Dancer should not dance too long without a break"""

    def check(self, graph: ScheduleGraph) -> list[Violation]:
        """Check for dancers dancing continuously for too long

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
            # Sort performances by start time
            performances = sorted(
                graph.get_performances_of_competitor(competitor),
                key=lambda p: self._ensure_datetime(p.start_time)
            )

            if len(performances) < 2:
                continue

            # Find continuous blocks of performances
            continuous_duration = performances[0].duration
            block_performances = [performances[0]]

            for i in range(1, len(performances)):
                prev = performances[i - 1]
                curr = performances[i]

                prev_end = self._ensure_datetime(prev.end_time)
                curr_start = self._ensure_datetime(curr.start_time)

                # If gap is less than 12 minutes, consider it continuous
                gap = (curr_start - prev_end).total_seconds() / 60

                if gap < self.config['rest_time']:
                    continuous_duration += curr.duration
                    block_performances.append(curr)
                else:
                    # Check completed block
                    violation = self._check_duration(
                        competitor, continuous_duration, block_performances
                    )
                    if violation:
                        violations.append(violation)

                    # Start new block
                    continuous_duration = curr.duration
                    block_performances = [curr]

            # Check last block
            violation = self._check_duration(
                competitor, continuous_duration, block_performances
            )
            if violation:
                violations.append(violation)

        return violations

    def _check_duration(self, competitor, duration, block_performances: list) -> Optional[Violation]:
        """Check if continuous duration exceeds thresholds

        Args:
            competitor: Competitor object
            duration: Duration of continuous dancing
            block_performances: All performances in the continuous block

        Returns:
            Violation object if threshold exceeded, None otherwise
        """
        severity = self._get_severity(duration)
        duration = int(duration)

        if severity:
            threshold = self.config['thresholds'][severity.value]
            excess = duration - threshold
            weight = self._calculate_weight(severity, excess)
            start_perf = block_performances[0]
            end_perf = block_performances[-1]

            return Violation(
                rule_name="MaxContinuousDancing",
                severity=severity,
                weight=weight,
                description=f"Tanečník {competitor.full_name_1} tančí {duration:.0f} minut bez přestávky",
                entity_id=competitor.full_name_1,
                entity_name=competitor.full_name_1,
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
