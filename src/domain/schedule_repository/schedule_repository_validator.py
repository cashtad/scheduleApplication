from __future__ import annotations

from .schedule_repository import ScheduleRepository
from .schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ScheduleRepositoryValidationReport,
    ValidationIssueSeverity,
)


class ScheduleRepositoryValidator:

    @staticmethod
    def check_performances_connection_to_competitions(repository: ScheduleRepository) -> list[
        ScheduleRepositoryValidationIssue]:
        issues: list[ScheduleRepositoryValidationIssue] = []
        competition_ids = set(repository.competitions_by_id.keys())

        for competition_id, performances in repository.performances_by_competition_id.items():
            if competition_id not in competition_ids:
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="UNKNOWN_COMPETITION_IN_PERFORMANCE",
                        message=f"Performance references unknown competition_id={competition_id}",
                        severity=ValidationIssueSeverity.ERROR,
                        context={"competition_id": competition_id},
                    )
                )

        return issues

    @staticmethod
    def check_duplicate_performances(repository: ScheduleRepository) -> list[ScheduleRepositoryValidationIssue]:
        issues: list[ScheduleRepositoryValidationIssue] = []
        seen_keys: set[tuple] = set()

        for value in repository.performances_by_competition_id.values():
            for performance in value:
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
                            message="Duplicate performance detected within competition",
                            severity=ValidationIssueSeverity.ERROR,
                            context={
                                "competition_id": performance.competition_id,
                                "source_row": performance.source_row,
                            },
                        )
                    )
                else:
                    seen_keys.add(key)
        return issues

    @staticmethod
    def check_competitors(repository: ScheduleRepository) -> list[ScheduleRepositoryValidationIssue]:

        issues: list[ScheduleRepositoryValidationIssue] = []

        competition_ids = set(repository.competitions_by_id.keys())

        for competitor in repository.competitors:
            missing = sorted(set(competitor.competition_ids) - competition_ids)
            if missing:
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="COMPETITOR_UNKNOWN_COMPETITION",
                        message=f"Competitor '{competitor.dancer_1_name}' references unknown competition ids",
                        severity=ValidationIssueSeverity.ERROR,
                        context={"missing_competition_ids": tuple(missing)},
                    )
                )

            if not repository.list_assignments_of_human(competitor):
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="COMPETITOR_WITHOUT_PERFORMANCES",
                        message=f"Competitor '{competitor.dancer_1_name}' has no performances in schedule",
                        severity=ValidationIssueSeverity.WARNING,
                        context={"competitor_name": competitor.dancer_1_name},
                    )
                )
        return issues

    @staticmethod
    def check_jury_members(repository: ScheduleRepository) -> list[ScheduleRepositoryValidationIssue]:
        issues: list[ScheduleRepositoryValidationIssue] = []

        competition_ids = set(repository.competitions_by_id.keys())

        for jury_member in repository.jury_members:
            missing = sorted(set(jury_member.competition_ids) - competition_ids)
            if missing:
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="JURY_UNKNOWN_COMPETITION",
                        message=f"Jury member '{jury_member.fullname}' references unknown competition ids",
                        severity=ValidationIssueSeverity.ERROR,
                        context={"missing_competition_ids": tuple(missing)},
                    )
                )

            if not repository.list_assignments_of_human(jury_member):
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="JURY_WITHOUT_PERFORMANCES",
                        message=f"Jury member '{jury_member.fullname}' has no performances in schedule",
                        severity=ValidationIssueSeverity.WARNING,
                        context={"jury_member_fullname": jury_member.fullname},
                    )
                )
        return issues

    @staticmethod
    def check_competitions_not_used(repository: ScheduleRepository) -> list[ScheduleRepositoryValidationIssue]:
        issues: list[ScheduleRepositoryValidationIssue] = []
        competition_ids = set(repository.competitions_by_id.keys())

        for competition_id in competition_ids:
            if not repository.list_performances_by_competition_id(competition_id):
                issues.append(
                    ScheduleRepositoryValidationIssue(
                        code="COMPETITION_WITHOUT_PERFORMANCES",
                        message=f"Competition id={competition_id} has no performances",
                        severity=ValidationIssueSeverity.WARNING,
                        context={"competition_id": competition_id},
                    )
                )
        return issues

    @staticmethod
    def validate(repository: ScheduleRepository) -> ScheduleRepositoryValidationReport:
        issues: list[ScheduleRepositoryValidationIssue] = []

        connection_issues = ScheduleRepositoryValidator.check_performances_connection_to_competitions(repository)
        issues.extend(connection_issues)

        duplicate_issues = ScheduleRepositoryValidator.check_duplicate_performances(repository)
        issues.extend(duplicate_issues)

        competitors_issues = ScheduleRepositoryValidator.check_competitors(repository)
        issues.extend(competitors_issues)

        jury_issues = ScheduleRepositoryValidator.check_jury_members(repository)
        issues.extend(jury_issues)

        competitions_issues = ScheduleRepositoryValidator().check_competitions_not_used(repository)
        issues.extend(competitions_issues)

        # Deduplicate
        unique: dict[tuple, ScheduleRepositoryValidationIssue] = {}
        for issue in issues:
            unique[issue.dedup_key()] = issue

        deduped_issues = list(unique.values())
        errors = [i for i in deduped_issues if i.severity == ValidationIssueSeverity.ERROR]
        warnings = [i for i in deduped_issues if i.severity == ValidationIssueSeverity.WARNING]

        return ScheduleRepositoryValidationReport(errors=errors, warnings=warnings)
