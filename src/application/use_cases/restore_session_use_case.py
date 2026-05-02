from __future__ import annotations

from src.application.contracts import all_table_keys
from src.application.ports import SessionStorePort
from src.application.services.table_status_transition_service import (
    TableStatusTransitionService,
)
from src.session import AppSession, TableRuntimeState
from src.session.app_session import SESSION_VERSION


class RestoreSessionUseCase:
    def __init__(
        self,
        session_store: SessionStorePort,
        transition_service: TableStatusTransitionService,
    ) -> None:
        self._session_store = session_store
        self._transition_service = transition_service

    def execute(self) -> AppSession:
        persisted = self._session_store.load()
        session = AppSession()
        session.ensure_required_tables()

        if persisted is None:
            return session

        is_compatible = persisted.version == SESSION_VERSION
        session.version = SESSION_VERSION
        session.saved_at = persisted.saved_at

        for table_key in all_table_keys():
            payload = persisted.tables.get(table_key)
            if payload is None:
                continue

            table = TableRuntimeState(
                table_key=table_key,
                file_path=payload.file_path,
                sheet_name=payload.sheet_name,
                column_mapping=(
                    dict(payload.column_mapping) if is_compatible else {}
                ),
                column_signature=(
                    list(payload.column_signature) if is_compatible else []
                ),
            )
            table.status = self._transition_service.infer_from_state(table)
            session.tables[table_key] = table

        return session

