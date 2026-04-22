from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.application.dto.data_quality_report import DataQualityReport
from src.domain import ScheduleAnalysisResult


class WorkflowStatus(Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"

@dataclass(frozen=True, slots=True)
class AnalyzeWorkflowResult:
    status: WorkflowStatus
    quality_report: DataQualityReport
    analysis_result: ScheduleAnalysisResult | None = None
    html_report_path: str | None = None
    error_message: str | None = None
