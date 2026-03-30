from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.application.ports.html_report_writer import HtmlReportWriter
from src.domain.analysis import ExplanationGenerator, ScheduleAnalysisResult


class HtmlExplanationReportWriter(HtmlReportWriter):
    def __init__(self, output_dir: str = ".reports") -> None:
        self._output_dir = Path(output_dir)
        self._generator = ExplanationGenerator()

    def write(self, analysis_result: ScheduleAnalysisResult) -> str:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self._output_dir / filename
        return self._generator.generate_html_report(analysis_result, str(output_path))