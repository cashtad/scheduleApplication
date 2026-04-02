from __future__ import annotations

from pathlib import Path

from src.infrastructure import SessionStore
from src.session import AppSession, REQUIRED_TABLE_KEYS, TableRuntimeState, TableStatus


class RestoreSessionUseCase:
    def __init__(self, session_store: SessionStore) -> None:
        self._session_store = session_store

    def execute(self) -> AppSession:
        persisted = self._session_store.load()
        session = AppSession()
        session.ensure_required_tables()

        if persisted is None:
            return session

        session.version = persisted.version
        session.saved_at = persisted.saved_at

        for table_key in REQUIRED_TABLE_KEYS:
            payload = persisted.tables.get(table_key)
            if payload is None:
                continue

            table = TableRuntimeState(
                table_key=table_key,
                file_path=payload.file_path,
                sheet_name=payload.sheet_name,
                column_mapping=dict(payload.column_mapping),
                column_signature=list(payload.column_signature),
            )
            table.status = self._infer_status(table)
            session.tables[table_key] = table

        return session

    @staticmethod
    def _infer_status(table: TableRuntimeState) -> TableStatus:
        if not table.file_path:
            return TableStatus.EMPTY

        if not Path(table.file_path).exists():
            return TableStatus.BROKEN_PATH

        if not table.sheet_name:
            return TableStatus.FILE_SELECTED

        if not table.column_mapping:
            return TableStatus.SHEET_SELECTED

        return TableStatus.MAPPED
