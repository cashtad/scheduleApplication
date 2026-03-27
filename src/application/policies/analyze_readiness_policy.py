from __future__ import annotations

from abc import ABC, abstractmethod

from ...domain.schedule_repository import ScheduleRepositoryValidationReport
from ..dto.prepare_data_result import PrepareDataResult
from ..dto.readiness import AnalyzeReadinessResult


class AnalyzeReadinessPolicy(ABC):
    @abstractmethod
    def evaluate(
        self,
        prepare_data_result: PrepareDataResult,
        repository_validation_report: ScheduleRepositoryValidationReport,
    ) -> AnalyzeReadinessResult:
        raise NotImplementedError