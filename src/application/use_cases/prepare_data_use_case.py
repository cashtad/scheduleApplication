from __future__ import annotations

from src.application.dto import PrepareDataResult
from src.application.services import TableInputFactory
from src.application.services.schedule_table_runtime_data_sync_service import (
    ScheduleTableRuntimeDataSyncService,
)
from src.application.services.session_status_sync_service import SessionStatusSyncService
from src.ingestion import TableIngestionService
from src.session import AppSession


class PrepareDataUseCase:
    def __init__(
        self,
        table_ingestion_service: TableIngestionService,
        session_status_sync_service: SessionStatusSyncService,
        session_runtime_data_sync_service: ScheduleTableRuntimeDataSyncService,
    ) -> None:
        self._table_ingestion_service = table_ingestion_service
        self._session_status_sync_service = session_status_sync_service
        self._session_runtime_data_sync_service = session_runtime_data_sync_service

    def execute(self, session: AppSession) -> PrepareDataResult:
        session.ensure_required_tables()

        inputs = TableInputFactory.build_for_tables(session)

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
