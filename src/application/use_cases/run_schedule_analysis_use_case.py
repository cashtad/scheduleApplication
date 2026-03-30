from __future__ import annotations

from dataclasses import dataclass

from ..dto import BuildRepositoryResult
from ..ports.html_report_writer import HtmlReportWriter
from src.domain.analysis import InferenceEngine, ScheduleAnalysisResult


@dataclass(frozen=True, slots=True)
class RunScheduleAnalysisResult:
    analysis_result: ScheduleAnalysisResult
    html_report_path: str | None = None


class RunScheduleAnalysisUseCase:
    def __init__(
        self,
        inference_engine: InferenceEngine,
        html_report_writer: HtmlReportWriter | None = None,
    ) -> None:
        self._inference_engine = inference_engine
        self._html_report_writer = html_report_writer

    def execute(self, build_repository_result: BuildRepositoryResult) -> RunScheduleAnalysisResult:
        analysis_result = self._inference_engine.analyze(build_repository_result.repository)

        html_report_path: str | None = None
        if self._html_report_writer is not None:
            html_report_path = self._html_report_writer.write(analysis_result)

        return RunScheduleAnalysisResult(
            analysis_result=analysis_result,
            html_report_path=html_report_path,
        )