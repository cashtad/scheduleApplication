from __future__ import annotations

from ..schedule_repository import ScheduleRepository
from ..schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ValidationIssueSeverity,
)


def check_performances_connection_to_competitions(
    repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
    issues: list[ScheduleRepositoryValidationIssue] = []
    competition_ids = set(repository.competitions_by_id)

    for competition_id in repository.performances_by_competition_id:
        if competition_id in competition_ids:
            continue

        issues.append(
            ScheduleRepositoryValidationIssue(
                code="UNKNOWN_COMPETITION_IN_PERFORMANCE",
                message=f"Vystoupení odkazuje na neznámé ID soutěže={competition_id}",
                severity=ValidationIssueSeverity.WARNING,
                context={"competition_id": competition_id},
            )
        )

    return issues




