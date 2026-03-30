from __future__ import annotations

from src.ingestion import FullIngestionResult, IngestionSeverity
from src.session import AppSession, REQUIRED_TABLE_KEYS, TableStatus


class SessionStatusSyncService:
    @staticmethod
    def sync_after_ingestion(session: AppSession, ingestion_result: FullIngestionResult) -> None:
        session.ensure_required_tables()

        schema_by_table: dict[str, list] = {}
        for issue in ingestion_result.schema_issues:
            schema_by_table.setdefault(issue.table_key, []).append(issue)

        for table_key in REQUIRED_TABLE_KEYS:
            table = session.get_table(table_key)
            issues = schema_by_table.get(table_key, [])

            if not table.file_path:
                table.status = TableStatus.EMPTY
                continue

            error_codes = {i.code for i in issues if i.severity == IngestionSeverity.ERROR}
            warning_codes = {i.code for i in issues if i.severity == IngestionSeverity.WARNING}

            if "FILE_NOT_FOUND" in error_codes or "FILE_PATH_EMPTY" in error_codes:
                table.status = TableStatus.BROKEN_PATH
                continue

            if "SHEET_NOT_FOUND" in error_codes or "SHEET_ENUMERATION_FAILED" in error_codes:
                table.status = TableStatus.BROKEN_SHEET
                continue

            if "COLUMN_SIGNATURE_MISMATCH" in warning_codes:
                table.status = TableStatus.MAPPING_STALE
                continue

            if table.column_mapping:
                table.status = TableStatus.READY
            elif table.sheet_name:
                table.status = TableStatus.SHEET_SELECTED
            else:
                table.status = TableStatus.FILE_SELECTED