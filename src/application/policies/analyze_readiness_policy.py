from __future__ import annotations

from abc import ABC, abstractmethod

from src.application.dto import AnalyzeReadinessResult, PrepareDataResult
from src.domain import ScheduleRepositoryValidationReport


class AnalyzeReadinessPolicy(ABC):
    @abstractmethod
    def evaluate(
        self,
        prepare_data_result: PrepareDataResult,
        repository_validation_report: ScheduleRepositoryValidationReport,
    ) -> AnalyzeReadinessResult:
        raise NotImplementedError