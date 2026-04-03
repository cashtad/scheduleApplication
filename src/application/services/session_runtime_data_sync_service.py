from __future__ import annotations

from pandas import DataFrame

from src.session import AppSession, REQUIRED_TABLE_KEYS


class SessionRuntimeDataSyncService:
    @staticmethod
    def sync_raw_tables(
        session: AppSession,
        raw_tables: dict[str, DataFrame],
    ) -> None:
        session.ensure_required_tables()
        for table_key in REQUIRED_TABLE_KEYS:
            session.get_table(table_key).raw_df = raw_tables.get(table_key)
