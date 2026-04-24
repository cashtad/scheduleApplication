from __future__ import annotations

from dataclasses import dataclass, field

from src.application.services import TableInputFactory
from src.application.services.session_status_sync_service import SessionStatusSyncService
from src.application.use_cases.save_session_use_case import SaveSessionUseCase
from src.ingestion import TableIngestionService
from src.session import AppSession, REQUIRED_TABLE_KEYS, TableStatus


@dataclass(frozen=True, slots=True)
class RevalidateSessionResult:
    statuses: dict[str, TableStatus] = field(default_factory=dict)


class RevalidateSessionUseCase:
    def __init__(
        self,
        table_ingestion_service: TableIngestionService,
        session_status_sync_service: SessionStatusSyncService,
        save_session_use_case: SaveSessionUseCase,
    ) -> None:
        self._table_ingestion_service = table_ingestion_service
        self._session_status_sync_service = session_status_sync_service
        self._save_session_use_case = save_session_use_case

    def execute(self, session: AppSession) -> RevalidateSessionResult:
        session.ensure_required_tables()

        inputs = TableInputFactory.build_for_required_tables(session)

        ingestion_result = self._table_ingestion_service.ingest(inputs)
        self._session_status_sync_service.sync_after_ingestion(
            session, ingestion_result
        )
        self._save_session_use_case.execute(session)

        return RevalidateSessionResult(
            statuses={k: session.get_table(k).status for k in REQUIRED_TABLE_KEYS}
        )
