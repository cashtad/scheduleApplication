from __future__ import annotations

from dataclasses import dataclass

from ...domain import ScheduleRepository, ScheduleRepositoryValidationReport


@dataclass(frozen=True, slots=True)
class BuildRepositoryResult:
    repository: ScheduleRepository
    validation_report: ScheduleRepositoryValidationReport
