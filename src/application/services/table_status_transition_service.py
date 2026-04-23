from __future__ import annotations

from pathlib import Path

from src.session import TableRuntimeState, TableStatus


class TableStatusTransitionService:
    def infer_from_state(self, table: TableRuntimeState) -> TableStatus:
        if not table.file_path:
            return TableStatus.EMPTY

        if not Path(table.file_path).exists():
            return TableStatus.BROKEN_PATH

        if not table.sheet_name:
            return TableStatus.FILE_SELECTED

        if not table.column_mapping:
            return TableStatus.SHEET_SELECTED

        return TableStatus.MAPPED

    def on_file_selected(self, table: TableRuntimeState) -> TableStatus:
        return TableStatus.FILE_SELECTED if table.file_path else TableStatus.EMPTY

    def on_sheet_selected(self, table: TableRuntimeState) -> TableStatus:
        if not table.file_path:
            return TableStatus.EMPTY
        if not table.sheet_name:
            return TableStatus.FILE_SELECTED
        return TableStatus.SHEET_SELECTED

    def on_mapping_applied(self, table: TableRuntimeState) -> TableStatus:
        if not table.file_path:
            return TableStatus.EMPTY
        if not table.sheet_name:
            return TableStatus.FILE_SELECTED
        if not table.column_mapping:
            return TableStatus.SHEET_SELECTED
        return TableStatus.MAPPED

    def on_mark_ready(self, table: TableRuntimeState) -> TableStatus:
        if table.file_path and table.sheet_name and table.column_mapping:
            return TableStatus.READY
        return self.infer_from_state(table)

    def on_ingestion_outcome(
        self,
        table: TableRuntimeState,
        error_codes: set[str],
        warning_codes: set[str],
    ) -> TableStatus:
        if "FILE_NOT_FOUND" in error_codes or "FILE_PATH_EMPTY" in error_codes:
            return TableStatus.BROKEN_PATH

        if "SHEET_NOT_FOUND" in error_codes or "SHEET_ENUMERATION_FAILED" in error_codes:
            return TableStatus.BROKEN_SHEET

        if "COLUMN_SIGNATURE_MISMATCH" in warning_codes:
            return TableStatus.MAPPING_STALE

        if error_codes:
            return self.on_mapping_applied(table)

        if table.column_mapping:
            return TableStatus.READY
        if table.sheet_name:
            return TableStatus.SHEET_SELECTED
        if table.file_path:
            return TableStatus.FILE_SELECTED
        return TableStatus.EMPTY

