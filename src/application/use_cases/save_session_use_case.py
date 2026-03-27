from __future__ import annotations

from datetime import datetime, timezone

from ...infrastructure import PersistedSession, PersistedTableState, SessionStore
from ...session import AppSession


class SaveSessionUseCase:
    def __init__(self, session_store: SessionStore) -> None:
        self._session_store = session_store

    def execute(self, session: AppSession) -> None:
        session.ensure_required_tables()

        persisted_tables: dict[str, PersistedTableState] = {}
        for table_key, table in session.tables.items():
            persisted_tables[table_key] = PersistedTableState(
                file_path=table.file_path,
                sheet_name=table.sheet_name,
                column_mapping=dict(table.column_mapping),
                column_signature=list(table.column_signature),
            )

        saved_at = datetime.now(timezone.utc).isoformat()
        persisted = PersistedSession(
            version=session.version,
            saved_at=saved_at,
            tables=persisted_tables,
        )
        self._session_store.save(persisted)
        session.saved_at = saved_at