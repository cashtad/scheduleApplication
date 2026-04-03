from __future__ import annotations

from src.application.dto import PrepareDataResult
from src.application.services import (
    SessionRuntimeDataSyncService,
    SessionStatusSyncService,
)
from src.ingestion import TableInput, TableIngestionService
from src.session import AppSession, REQUIRED_TABLE_KEYS


class PrepareDataUseCase:
    def __init__(
        self,
        table_ingestion_service: TableIngestionService,
        session_status_sync_service: SessionStatusSyncService,
        session_runtime_data_sync_service: SessionRuntimeDataSyncService,
    ) -> None:
        self._table_ingestion_service = table_ingestion_service
        self._session_status_sync_service = session_status_sync_service
        self._session_runtime_data_sync_service = session_runtime_data_sync_service

    def execute(self, session: AppSession) -> PrepareDataResult:
        session.ensure_required_tables()

        inputs: list[TableInput] = []
        for table_key in REQUIRED_TABLE_KEYS:
            ts = session.get_table(table_key)
            if not ts.file_path:
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

        ingestion_result = self._table_ingestion_service.ingest(inputs)
        self._session_status_sync_service.sync_after_ingestion(
            session, ingestion_result
        )
        self._session_runtime_data_sync_service.sync_raw_tables(
            session, ingestion_result.raw_tables
        )

        return PrepareDataResult(
            competitions=ingestion_result.competitions.items,
            competitors=ingestion_result.competitors.items,
            jury_members=ingestion_result.jury_members.items,
            performances=ingestion_result.performances.items,
            schema_issues=ingestion_result.schema_issues,
            row_issues=ingestion_result.all_row_issues,
            table_stats=ingestion_result.table_stats,
        )
