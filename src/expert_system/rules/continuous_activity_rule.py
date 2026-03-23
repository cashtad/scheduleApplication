from abc import ABC
from typing import Optional

from classes import Performance
from .rule import ARule
from .violation import Violation


class ContinuousActivityRule(ARule, ABC):
    """Base class for rules that detect excessively long continuous activity blocks."""

    def _collect_violations_for_continuous_blocks(
        self,
        performances: list[Performance],
        check_block_fn,
    ) -> list[Violation]:
        """Group performances into continuous blocks and check each block.

        A new block starts when the gap between two consecutive performances
        exceeds `rest_time` from config.

        Args:
            performances: Performances sorted by start time.
            check_block_fn: Callable(duration, block_performances) -> Optional[Violation]
        """
        if not performances:
            return []

        violations = []
        block_duration     = performances[0].duration
        block_performances = [performances[0]]

        for prev, curr in zip(performances, performances[1:]):
            prev_end   = self._ensure_datetime(prev.end_time)
            curr_start = self._ensure_datetime(curr.start_time)
            gap        = (curr_start - prev_end).total_seconds() / 60

            if gap < self.config["rest_time"]:
                block_duration += curr.duration
                block_performances.append(curr)
            else:
                violation = check_block_fn(block_duration, block_performances)
                if violation:
                    violations.append(violation)
                block_duration     = curr.duration
                block_performances = [curr]

        # Check the last (or only) block
        violation = check_block_fn(block_duration, block_performances)
        if violation:
            violations.append(violation)

        return violations

    def _build_duration_violation(
        self,
        duration: float,
        block_performances: list,
        rule_name: str,
        entity_id: str,
        entity_name: str,
        description: str,
    ) -> Optional[Violation]:
        """Build a Violation if the block duration exceeds configured thresholds.

        Returns None if duration is within acceptable limits.
        """
        severity = self._get_severity(duration)
        if severity is None:
            return None

        duration    = int(duration)
        threshold   = self.config["thresholds"][severity.value]
        excess      = duration - threshold
        weight      = self._calculate_weight(severity, excess)
        start_perf  = block_performances[0]
        end_perf    = block_performances[-1]

        return Violation(
            rule_name=rule_name,
            severity=severity,
            weight=weight,
            description=description,
            entity_id=entity_id,
            entity_name=entity_name,
            details={
                "duration_minutes":  duration,
                "threshold_minutes": threshold,
                "excess_minutes":    excess,
                "start_time":        self._ensure_datetime(start_perf.start_time),
                "end_time":          self._ensure_datetime(end_perf.end_time),
            },
            source_rows=self._source_rows(*block_performances),
        )