from __future__ import annotations

from collections.abc import Callable

from .schedule_repository import ScheduleRepository
from .schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ScheduleRepositoryValidationReport,
    ValidationIssueSeverity,
)
from .validation_checks import (
    check_amount_of_rounds,
    check_competitions_not_empty,
    check_competitions_not_used,
    check_competitors,
    check_competitors_not_empty,
    check_duplicate_performances,
    check_jury_members,
    check_jury_members_not_empty,
    check_performances_connection_to_competitions,
    check_performances_not_empty,
)

ValidationCheck = Callable[
    [ScheduleRepository],
    list[ScheduleRepositoryValidationIssue],
]


class ScheduleRepositoryValidator:
    _CHECK_PIPELINE: tuple[ValidationCheck, ...] = (
        check_performances_connection_to_competitions,
        check_duplicate_performances,
        check_competitors,
        check_jury_members,
        check_competitions_not_used,
        check_jury_members_not_empty,
        check_competitions_not_empty,
        check_performances_not_empty,
        check_competitors_not_empty,
        check_amount_of_rounds,
    )

    @staticmethod
    def _run_checks_in_order(
        repository: ScheduleRepository,
    ) -> list[ScheduleRepositoryValidationIssue]:
        issues: list[ScheduleRepositoryValidationIssue] = []

        for check in ScheduleRepositoryValidator._CHECK_PIPELINE:
            issues.extend(check(repository))

        return issues

    @staticmethod
    def _deduplicate_issues(
        issues: list[ScheduleRepositoryValidationIssue],
    ) -> list[ScheduleRepositoryValidationIssue]:
        unique: dict[tuple, ScheduleRepositoryValidationIssue] = {}
        for issue in issues:
            unique[issue.dedup_key()] = issue
        return list(unique.values())

    @staticmethod
    def _split_by_severity(
        issues: list[ScheduleRepositoryValidationIssue],
    ) -> tuple[list[ScheduleRepositoryValidationIssue], list[ScheduleRepositoryValidationIssue]]:
        errors = [i for i in issues if i.severity == ValidationIssueSeverity.ERROR]
        warnings = [i for i in issues if i.severity == ValidationIssueSeverity.WARNING]
        return errors, warnings


    @staticmethod
    def validate(repository: ScheduleRepository) -> ScheduleRepositoryValidationReport:
        issues = ScheduleRepositoryValidator._run_checks_in_order(repository)
        deduped_issues = ScheduleRepositoryValidator._deduplicate_issues(issues)
        errors, warnings = ScheduleRepositoryValidator._split_by_severity(deduped_issues)

        return ScheduleRepositoryValidationReport(errors=errors, warnings=warnings)
