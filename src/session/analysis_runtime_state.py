from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)  
class AnalysisRuntimeState:
    is_stale: bool = True
    last_html_report_path: str | None = None
    last_data_quality_report_path: str | None = None
    last_error_message: str | None = None