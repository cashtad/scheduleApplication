from __future__ import annotations

from abc import ABC
from typing import Callable

from src.domain import Performance
from .rule import ARule
from ..analysis import Violation


class ContinuousActivityRule(ARule, ABC):
    #TODO: fix thresholds and excess

    def _collect_violations_for_continuous_blocks(
        self,
        performances: list[Performance],
        check_block_fn: Callable[[float, list[Performance]], Violation | None],
    ) -> list[Violation]:
        if not performances:
            return []

        violations: list[Violation] = []
        block_duration = performances[0].duration
        block_performances: list[Performance] = [performances[0]]

        for prev, curr in zip(performances, performances[1:]):
            prev_end = self._ensure_datetime(prev.end_time)
            curr_start = self._ensure_datetime(curr.start_time)
            gap_minutes = (curr_start - prev_end).total_seconds() / 60

            if int(gap_minutes) < self.config.rest_time:
                block_duration += curr.duration
                block_performances.append(curr)
            else:
                maybe = check_block_fn(block_duration, block_performances)
                if maybe is not None:
                    violations.append(maybe)
                block_duration = curr.duration
                block_performances = [curr]

        maybe_last = check_block_fn(block_duration, block_performances)
        if maybe_last is not None:
            violations.append(maybe_last)

        return violations

    def _build_duration_violation(
        self,
        duration: float,
        block_performances: list[Performance],
        rule_name: str,
        entity_id: str,
        entity_name: str,
        description: str,
    ) -> Violation | None:
        severity = self._get_severity(duration)
        if severity is None:
            return None

        duration_i = int(duration)
        threshold = int(self.config["thresholds"][severity.value])
        excess = duration_i - threshold

        start_perf = block_performances[0]
        end_perf = block_performances[-1]

        return Violation(
            rule_name=rule_name,
            severity=severity,
            description=description,
            entity_id=entity_id,
            entity_name=entity_name,
            details={
                "duration_minutes": duration_i,
                "threshold_minutes": threshold,
                "excess_minutes": excess,
                "start_time": self._ensure_datetime(start_perf.start_time),
                "end_time": self._ensure_datetime(end_perf.end_time),
            },
            source_rows=self._source_rows(*block_performances),
        )