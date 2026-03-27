from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..dto import BuildRepositoryResult


@dataclass(frozen=True, slots=True)
class RunScheduleAnalysisResult:
    analysis_result: Any
    html_report_path: str | None = None


class RunScheduleAnalysisUseCase:
    def __init__(self) -> None:
        raise NotImplementedError

    def execute(self, build_repository_result: BuildRepositoryResult) -> RunScheduleAnalysisResult:
        # TODO (next step):
        # 1) analysis_result = self._analyzer.analyze(build_repository_result.repository)
        # return RunScheduleAnalysisResult(...)
        raise NotImplementedError