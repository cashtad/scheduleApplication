from __future__ import annotations

from typing import Protocol

from src.domain import ScheduleAnalysisResult


class HtmlReportWriterPort(Protocol):
    def write(self, analysis_result: ScheduleAnalysisResult) -> str: ...
