from __future__ import annotations

from abc import ABC, abstractmethod

from ...domain import ScheduleRepositoryValidationReport
from ..dto import PrepareDataResult, AnalyzeReadinessResult

class AnalyzeReadinessPolicy(ABC):
    @abstractmethod
    def evaluate(
        self,
        prepare_data_result: PrepareDataResult,
        repository_validation_report: ScheduleRepositoryValidationReport,
    ) -> AnalyzeReadinessResult:
        raise NotImplementedError