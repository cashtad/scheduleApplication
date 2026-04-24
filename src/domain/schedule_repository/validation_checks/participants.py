from __future__ import annotations

from ..schedule_repository import ScheduleRepository
from ..schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ValidationIssueSeverity,
)


def check_competitors(
    repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
    issues: list[ScheduleRepositoryValidationIssue] = []
    competition_ids = set(repository.competitions_by_id)

    for competitor in repository.competitors:
        missing = sorted(set(competitor.competition_ids) - competition_ids)
        if missing:
            issues.append(
                ScheduleRepositoryValidationIssue(
                    code="COMPETITOR_UNKNOWN_COMPETITION",
                    message=f"Soutěžící '{competitor.dancer_1_name}' odkazuje na neznámá ID soutěží {missing}",
                    severity=ValidationIssueSeverity.ERROR,
                    context={"missing_competition_ids": tuple(missing)},
                )
            )

        if repository.list_assignments_of_human(competitor):
            continue

        issues.append(
            ScheduleRepositoryValidationIssue(
                code="COMPETITOR_WITHOUT_PERFORMANCES",
                message=f"Soutěžící '{competitor.dancer_1_name}' nemá v harmonogramu žádná vystoupení",
                severity=ValidationIssueSeverity.WARNING,
                context={"competitor_name": competitor.dancer_1_name},
            )
        )

    return issues


def check_jury_members(
    repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
    issues: list[ScheduleRepositoryValidationIssue] = []
    competition_ids = set(repository.competitions_by_id)

    for jury_member in repository.jury_members:
        missing = sorted(set(jury_member.competition_ids) - competition_ids)
        if missing:
            issues.append(
                ScheduleRepositoryValidationIssue(
                    code="JURY_UNKNOWN_COMPETITION",
                    message=f"Člen poroty '{jury_member.fullname}' odkazuje na neznámá ID soutěží {missing}",
                    severity=ValidationIssueSeverity.WARNING,
                    context={"missing_competition_ids": tuple(missing)},
                )
            )

        if repository.list_assignments_of_human(jury_member):
            continue

        issues.append(
            ScheduleRepositoryValidationIssue(
                code="JURY_WITHOUT_PERFORMANCES",
                message=f"Člen poroty '{jury_member.fullname}' nemá v harmonogramu žádná vystoupení",
                severity=ValidationIssueSeverity.WARNING,
                context={"jury_member_fullname": jury_member.fullname},
            )
        )

    return issues



