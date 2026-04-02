from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pandas import DataFrame

from application.bootstrap import AppContainer, build_app_container
from application.dto import (
    AnalyzeWorkflowResult,
    AnalysisViewModel,
    build_analysis_view_model,
)
from application.services.session_service import SessionService
from session import AppSession, REQUIRED_TABLE_KEYS, TableStatus
from src.infrastructure import PandasExcelReader


class UiController:
    def __init__(
        self,
        rules_config_path: str | Path,
        *,
        reports_dir: str = ".reports",
        with_html_report_writer: bool = True,
        row_error_threshold: float = 0.5,
    ) -> None:
        self._container: AppContainer = build_app_container(
            rules_config_path=rules_config_path,
            reports_dir=reports_dir,
            with_html_report_writer=with_html_report_writer,
            row_error_threshold=row_error_threshold,
        )
        self._session_service = SessionService(self._container.save_session_use_case)
        self._session: AppSession = self._container.restore_session_use_case.execute()
        self._last_workflow_result: AnalyzeWorkflowResult | None = None
        self._last_analysis_view: AnalysisViewModel | None = None
        self.excel_reader = PandasExcelReader()

    @property
    def session(self) -> AppSession:
        return self._session

    @property
    def last_workflow_result(self) -> AnalyzeWorkflowResult | None:
        return self._last_workflow_result

    @property
    def last_analysis_view(self) -> AnalysisViewModel | None:
        return self._last_analysis_view

    def read(self, file_path: str, sheet_name: str | None) -> DataFrame:
        return self.excel_reader.read(file_path, sheet_name)

    def get_sheet_names(self, file_path: str) -> list[str]:
        return self.excel_reader.get_sheet_names(file_path)

    def required_table_keys(self) -> tuple[str, ...]:
        return REQUIRED_TABLE_KEYS

    def get_table_status(self, table_key: str) -> TableStatus:
        return self._session.get_table(table_key).status

    def get_table_statuses(self) -> dict[str, TableStatus]:
        return {k: self._session.get_table(k).status for k in REQUIRED_TABLE_KEYS}

    def set_file(self, table_key: str, file_path: str) -> None:
        self._session_service.set_file(self._session, table_key, file_path)

    def set_sheet(self, table_key: str, sheet_name: str) -> None:
        self._session_service.set_sheet(self._session, table_key, sheet_name)

    def set_mapping(
        self,
        table_key: str,
        column_mapping: dict[str, str],
        current_columns: Iterable[str],
    ) -> None:
        self._session_service.set_mapping(
            session=self._session,
            table_key=table_key,
            column_mapping=column_mapping,
            current_columns=current_columns,
        )

    def mark_ready(self, table_key: str) -> None:
        self._session_service.mark_ready(self._session, table_key)

    def can_run_analysis(self) -> bool:
        return self._session.is_ready_to_analyze()

    def run_analysis(self) -> AnalyzeWorkflowResult:
        result = self._container.analyze_workflow_service.run_analysis(self._session)
        self._last_workflow_result = result
        if result.analysis_result is not None:
            self._last_analysis_view = build_analysis_view_model(result.analysis_result)
        else:
            self._last_analysis_view = None
        return result
