from __future__ import annotations

from ..schedule_repository import ScheduleRepository
from ..schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ValidationIssueSeverity,
)


def check_amount_of_rounds(
    repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
    issues: list[ScheduleRepositoryValidationIssue] = []

    for competition in repository.competitions_by_id.values():
        performances = repository.list_performances_by_competition_id(competition.id)
        actual_amount = len(performances)
        expected_amount = competition.amount_of_rounds

        if not expected_amount or expected_amount == actual_amount:
            continue

        issues.append(
            ScheduleRepositoryValidationIssue(
                code="WRONG_AMOUNT_OF_ROUNDS",
                message=f"Soutěž '{competition.name}' (ID: {competition.id}) má v harmonogramu {actual_amount} kol/vystoupení, ale v informacích o soutěži je očekáváno {expected_amount}.",
                severity=ValidationIssueSeverity.WARNING,
                context={
                    "competition_id": competition.id,
                    "expected_amount_of_rounds": expected_amount,
                    "actual_amount_of_rounds": actual_amount,
                },
            )
        )

    return issues


