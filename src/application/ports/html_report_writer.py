from __future__ import annotations

from typing import Protocol

from src.domain.analysis import ScheduleAnalysisResult


class HtmlReportWriter(Protocol):
    def write(self, analysis_result: ScheduleAnalysisResult) -> str:
        ...