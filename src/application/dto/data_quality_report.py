from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .prepare_data_result import PrepareDataResult
from .readiness import AnalyzeReadinessResult
from ...domain import ScheduleRepositoryValidationReport


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    generated_at: datetime
    row_error_threshold: float
    prepare_data_result: PrepareDataResult
    repository_validation_report: ScheduleRepositoryValidationReport
    readiness_result: AnalyzeReadinessResult
