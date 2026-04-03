from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.application.dto.prepare_data_result import PrepareDataResult
from src.application.dto.readiness import AnalyzeReadinessResult
from src.domain import ScheduleRepositoryValidationReport


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    generated_at: datetime
    row_error_threshold: float
    prepare_data_result: PrepareDataResult
    repository_validation_report: ScheduleRepositoryValidationReport
    readiness_result: AnalyzeReadinessResult
