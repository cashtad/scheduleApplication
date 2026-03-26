from __future__ import annotations

from ...domain.schedule_repository import ScheduleRepositoryValidationReport
from ..dto.prepare_data_result import PrepareDataResult #TODO: fix from
from ..dto.readiness import AnalyzeReadinessResult


class AnalyzeReadinessPolicy:
    def evaluate(
        self,
        prepare_data_result: PrepareDataResult,
        repository_validation_report: ScheduleRepositoryValidationReport,
    ) -> AnalyzeReadinessResult:
        raise NotImplementedError