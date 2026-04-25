from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pandas import DataFrame

from src.application.bootstrap import AppContainer, build_app_container
from src.application.ports import ExcelReaderPort
from src.application.dto import (
    AnalyzeWorkflowResult,
    AnalysisViewModel,
    DataQualityReport,
    build_analysis_view_model,
    WorkflowStatus
)
from src.application.services import MappingValidationService
from src.application.contracts import TableKey, required_table_keys
from src.session import AppSession, TableRuntimeState, TableStatus


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
        self._session_service = self._container.session_service
        self._mapping_validation_service = MappingValidationService()

        self._session: AppSession = self._container.restore_session_use_case.execute()
        self._container.revalidate_session_use_case.execute(self._session)

        self._last_workflow_result: AnalyzeWorkflowResult | None = None
        self._last_analysis_view: AnalysisViewModel | None = None
        self._excel_reader: ExcelReaderPort = self._container.excel_reader

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
        return self._excel_reader.read(file_path, sheet_name)

    def get_sheet_names(self, file_path: str) -> list[str | int]:
        return self._excel_reader.get_sheet_names(file_path)

    def required_table_keys(self) -> tuple[TableKey, ...]:
        return required_table_keys()

    def get_table_state(self, table_key: TableKey) -> TableRuntimeState:
        return self._session.get_table(table_key)

    def get_table_statuses(self) -> dict[str, TableStatus]:
        return {k: self._session.get_table(k).status for k in required_table_keys()}

    def set_file(self, table_key: TableKey, file_path: str) -> None:
        self._session_service.set_file(self._session, table_key, file_path)

    def set_sheet(self, table_key: TableKey, sheet_name: str) -> None:
        self._session_service.set_sheet(self._session, table_key, sheet_name)

    def set_mapping(
        self,
        table_key: TableKey,
        column_mapping: dict[str, str],
        current_columns: Iterable[str],
    ) -> None:
        self._session_service.set_mapping(
            session=self._session,
            table_key=table_key,
            column_mapping=column_mapping,
            current_columns=current_columns,
        )

    def mark_ready(self, table_key: TableKey) -> None:
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

    def validate_mapping_preflight(
        self,
        table_key: TableKey,
        mapping: dict[str, str],
        current_columns: list[str],
    ) -> tuple[bool, str]:
        check = self._mapping_validation_service.validate_mapping(
            table_key=table_key,
            mapping=mapping,
            current_columns=current_columns,
        )
        return check.is_valid, check.message

    def get_applicable_saved_mapping(
        self,
        table_key: TableKey,
        current_columns: list[str],
    ) -> dict[str, str] | None:
        table = self._session.get_table(table_key)
        return self._mapping_validation_service.get_applicable_saved_mapping(
            table_state=table,
            current_columns=current_columns,
        )

    def get_applicable_mapping_for_columns(
        self,
        table_key: TableKey,
        mapping: dict[str, str],
        current_columns: list[str],
    ) -> dict[str, str] | None:
        if not mapping:
            return None
        ok, _ = self.validate_mapping_preflight(table_key, mapping, current_columns)
        return dict(mapping) if ok else None

    def apply_mapping_and_mark_ready(
        self,
        table_key: TableKey,
        mapping: dict[str, str],
        current_columns: list[str],
    ) -> tuple[bool, str]:
        ok, message = self.validate_mapping_preflight(
            table_key, mapping, current_columns
        )
        if not ok:
            return False, message

        self.set_mapping(table_key, mapping, current_columns)
        self.mark_ready(table_key)
        return True, ""

    def get_last_schedule_df(self) -> DataFrame | None:
        return self._session.get_table(TableKey.SCHEDULE).raw_df

    # --- Data quality / report helpers ---

    def get_last_workflow_status(self) -> WorkflowStatus | None:
        return self._last_workflow_result.status if self._last_workflow_result else None

    def get_last_quality_report(self) -> DataQualityReport | None:
        return (
            self._last_workflow_result.quality_report
            if self._last_workflow_result
            else None
        )

    def get_last_html_report_path(self) -> str | None:
        if not self._last_workflow_result:
            return None
        return self._last_workflow_result.html_report_path
