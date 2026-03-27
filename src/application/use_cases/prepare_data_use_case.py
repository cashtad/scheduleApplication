from __future__ import annotations

from ..dto.prepare_data_result import PrepareDataResult
from ...ingestion.contracts.table_input import TableInput
from ...ingestion.services.table_ingestion_service import TableIngestionService
from ...session.app_session import AppSession, REQUIRED_TABLE_KEYS
from ...session.table_status import TableStatus


class PrepareDataUseCase:
    def __init__(self, table_ingestion_service: TableIngestionService) -> None:
        self._table_ingestion_service = table_ingestion_service

    def execute(self, session: AppSession) -> PrepareDataResult:
        session.ensure_required_tables()

        inputs: list[TableInput] = []
        for table_key in REQUIRED_TABLE_KEYS:
            ts = session.get_table(table_key)
            if not ts.file_path:
                ts.status = TableStatus.EMPTY
                continue

            inputs.append(
                TableInput(
                    table_key=table_key,
                    file_path=ts.file_path,
                    sheet_name=ts.sheet_name,
                    mapping=dict(ts.column_mapping),
                    column_signature=list(ts.column_signature),
                )
            )

        ingestion_result = self._table_ingestion_service.ingest(inputs=inputs)
        self._sync_table_statuses(session=session, prepare_from=ingestion_result)

        return PrepareDataResult(
            competitions=ingestion_result.competitions.items,
            competitors=ingestion_result.competitors.items,
            jury_members=ingestion_result.jury_members.items,
            performances=ingestion_result.performances.items,
            schema_issues=ingestion_result.schema_issues,
            row_issues=ingestion_result.all_row_issues,
            table_stats=ingestion_result.table_stats,
        )

    def _sync_table_statuses(self, session: AppSession, prepare_from) -> None:
        # Build fast index of schema issues per table
        schema_by_table: dict[str, list] = {}
        for issue in prepare_from.schema_issues:
            schema_by_table.setdefault(issue.table_key, []).append(issue)

        for key in REQUIRED_TABLE_KEYS:
            table = session.get_table(key)
            issues = schema_by_table.get(key, [])

            if table.status == TableStatus.EMPTY and not table.file_path:
                continue

            error_codes = {i.code for i in issues if i.severity.value == "error"}
            warning_codes = {i.code for i in issues if i.severity.value == "warning"}

            if "FILE_NOT_FOUND" in error_codes or "FILE_PATH_EMPTY" in error_codes:
                table.status = TableStatus.BROKEN_PATH
                continue

            if "SHEET_NOT_FOUND" in error_codes or "SHEET_ENUMERATION_FAILED" in error_codes:
                table.status = TableStatus.BROKEN_SHEET
                continue

            if "COLUMN_SIGNATURE_MISMATCH" in warning_codes:
                table.status = TableStatus.MAPPING_STALE
                continue

            # If mapping exists and no schema blockers => ready for analysis pipeline
            if table.column_mapping:
                table.status = TableStatus.READY
            elif table.sheet_name:
                table.status = TableStatus.SHEET_SELECTED
            else:
                table.status = TableStatus.FILE_SELECTED