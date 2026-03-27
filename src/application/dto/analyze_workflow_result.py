from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_quality_report import DataQualityReport
from .workflow_status import WorkflowStatus


@dataclass(frozen=True, slots=True)
class AnalyzeWorkflowResult:
    status: WorkflowStatus
    quality_report: DataQualityReport
    analysis_result: Any | None = None
    html_report_path: str | None = None
    error_message: str | None = None
