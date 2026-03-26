from __future__ import annotations

from ...domain.schedule_repository import ScheduleRepositoryValidationReport
from .prepare_data_result import PrepareDataResult
from .readiness import AnalyzeReadinessResult


class AnalyzeReadinessPolicy:
    def evaluate(
        self,
        prepare_data_result: PrepareDataResult,
        repository_validation_report: ScheduleRepositoryValidationReport,
    ) -> AnalyzeReadinessResult:
        raise NotImplementedError