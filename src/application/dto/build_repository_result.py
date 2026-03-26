from __future__ import annotations

from dataclasses import dataclass

from ...domain.schedule_repository import ScheduleRepository, ScheduleRepositoryValidationReport


@dataclass(frozen=True, slots=True)
class BuildRepositoryResult:
    repository: ScheduleRepository
    validation_report: ScheduleRepositoryValidationReport