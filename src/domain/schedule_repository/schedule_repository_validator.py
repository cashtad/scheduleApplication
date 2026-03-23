from __future__ import annotations

from .schedule_repository import ScheduleRepository
from .schedule_repository_validation import (
    ScheduleRepositoryValidationIssue,
    ScheduleRepositoryValidationReport,
    ValidationIssueSeverity,
)


class ScheduleRepositoryValidator:
    @staticmethod
    def validate(repository: ScheduleRepository) -> ScheduleRepositoryValidationReport:
        errors: list[ScheduleRepositoryValidationIssue] = []
        warnings: list[ScheduleRepositoryValidationIssue] = []

        competition_ids = set(repository.competitions_by_id.keys())

        for competition_id, performances in repository.performances_by_competition_id.items():
            if competition_id not in competition_ids:
                errors.append(
                    ScheduleRepositoryValidationIssue(
                        code="UNKNOWN_COMPETITION_IN_PERFORMANCE",
                        message=f"Performance references unknown competition_id={competition_id}",
                        severity=ValidationIssueSeverity.ERROR,
                        context={"competition_id": competition_id},
                    )
                )

            seen_keys: set[tuple] = set()
            for perf in performances:
                key = (perf.competition_id, perf.start_time, perf.end_time, perf.round_type)
                if key in seen_keys:
                    errors.append(
                        ScheduleRepositoryValidationIssue(
                            code="DUPLICATE_PERFORMANCE",
                            message="Duplicate performance detected",
                            severity=ValidationIssueSeverity.ERROR,
                            context={"competition_id": perf.competition_id, "source_row": perf.source_row},
                        )
                    )
                else:
                    seen_keys.add(key)

        for competitor in repository.competitors:
            missing = sorted(set(competitor.competition_ids) - competition_ids)
            if missing:
                errors.append(
                    ScheduleRepositoryValidationIssue(
                        code="COMPETITOR_UNKNOWN_COMPETITION",
                        message=f"Competitor '{competitor.dancer_1_name}' references unknown competition ids",
                        severity=ValidationIssueSeverity.ERROR,
                        context={"missing_competition_ids": missing},
                    )
                )
            if not repository.list_assignments_of_human(competitor):
                warnings.append(
                    ScheduleRepositoryValidationIssue(
                        code="COMPETITOR_WITHOUT_PERFORMANCES",
                        message=f"Competitor '{competitor.dancer_1_name}' has no performances in schedule",
                        severity=ValidationIssueSeverity.WARNING,
                        context={"competitor": competitor.dancer_1_name},
                    )
                )

        for jury_member in repository.jury_members:
            missing = sorted(set(jury_member.competition_ids) - competition_ids)
            if missing:
                errors.append(
                    ScheduleRepositoryValidationIssue(
                        code="JURY_UNKNOWN_COMPETITION",
                        message=f"Jury member '{jury_member.fullname}' references unknown competition ids",
                        severity=ValidationIssueSeverity.ERROR,
                        context={"missing_competition_ids": missing},
                    )
                )
            if not repository.list_assignments_of_human(jury_member):
                warnings.append(
                    ScheduleRepositoryValidationIssue(
                        code="JURY_WITHOUT_PERFORMANCES",
                        message=f"Jury member '{jury_member.fullname}' has no performances in schedule",
                        severity=ValidationIssueSeverity.WARNING,
                        context={"jury_member": jury_member.fullname},
                    )
                )

        for competition_id in competition_ids:
            if len(repository.find_performances_by_competition_id(competition_id)) == 0:
                warnings.append(
                    ScheduleRepositoryValidationIssue(
                        code="COMPETITION_WITHOUT_PERFORMANCES",
                        message=f"Competition id={competition_id} has no performances",
                        severity=ValidationIssueSeverity.WARNING,
                        context={"competition_id": competition_id},
                    )
                )

        return ScheduleRepositoryValidationReport(errors=errors, warnings=warnings)