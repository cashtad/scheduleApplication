from __future__ import annotations

from dataclasses import dataclass

from src.application.dto.data_quality_report import DataQualityReport
from src.application.dto.workflow_status import WorkflowStatus
from src.domain import ScheduleAnalysisResult


@dataclass(frozen=True, slots=True)
class AnalyzeWorkflowResult:
    status: WorkflowStatus
    quality_report: DataQualityReport
    analysis_result: ScheduleAnalysisResult | None = None
    html_report_path: str | None = None
    error_message: str | None = None
