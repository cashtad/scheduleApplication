from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..dto.build_repository_result import BuildRepositoryResult


@dataclass(frozen=True, slots=True)
class RunScheduleAnalysisResult:
    analysis_result: Any
    html_report_path: str | None = None


class RunScheduleAnalysisUseCase:
    """
    Runs schedule analysis on validated repository and optionally writes HTML report.
    """

    def __init__(self, analyzer, html_report_writer) -> None:
        self._analyzer = analyzer
        self._html_report_writer = html_report_writer

    def execute(self, build_repository_result: BuildRepositoryResult) -> RunScheduleAnalysisResult:
        # TODO (next step):
        # 1) analysis_result = self._analyzer.analyze(build_repository_result.repository)
        # 2) html_path = self._html_report_writer.write(analysis_result)
        # 3) return RunScheduleAnalysisResult(...)
        raise NotImplementedError