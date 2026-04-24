from __future__ import annotations

from ..schedule_repository import ScheduleRepository
from ..schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ValidationIssueSeverity,
)


def check_duplicate_performances(
    repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
    issues: list[ScheduleRepositoryValidationIssue] = []
    seen_keys: set[tuple] = set()

    for performances in repository.performances_by_competition_id.values():
        for performance in performances:
            key = (
                performance.competition_id,
                performance.start_time,
                performance.end_time,
                performance.round_type.strip().lower(),
            )
            if key in seen_keys:
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="DUPLICATE_PERFORMANCE",
                        message="Bylo nalezeno duplicitní vystoupení v rámci soutěže",
                        severity=ValidationIssueSeverity.ERROR,
                        context={
                            "competition_id": performance.competition_id,
                            "source_row": performance.source_row,
                        },
                    )
                )
                continue

            seen_keys.add(key)

    return issues


