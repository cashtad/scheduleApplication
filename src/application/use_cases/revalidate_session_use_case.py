from __future__ import annotations

from dataclasses import dataclass, field

from src.application.services import SessionStatusSyncService
from src.ingestion import TableInput, TableIngestionService
from src.session import AppSession, REQUIRED_TABLE_KEYS, TableStatus
from .save_session_use_case import SaveSessionUseCase


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

        inputs: list[TableInput] = []
        for table_key in REQUIRED_TABLE_KEYS:
            table = session.get_table(table_key)
            if not table.file_path:
                continue

            inputs.append(
                TableInput(
                    table_key=table_key,
                    file_path=table.file_path,
                    sheet_name=table.sheet_name,
                    mapping=dict(table.column_mapping),
                    column_signature=list(table.column_signature),
                )
            )

        ingestion_result = self._table_ingestion_service.ingest(inputs)
        self._session_status_sync_service.sync_after_ingestion(
            session, ingestion_result
        )
        self._save_session_use_case.execute(session)

        return RevalidateSessionResult(
            statuses={k: session.get_table(k).status for k in REQUIRED_TABLE_KEYS}
        )
