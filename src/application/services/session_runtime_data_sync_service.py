from __future__ import annotations

from pandas import DataFrame

from src.session import AppSession


class SessionRuntimeDataSyncService:
    # only schedule table is needed, but it can save all tables
    @staticmethod
    def sync_raw_tables(
        session: AppSession,
        raw_tables: dict[str, DataFrame | None],
    ) -> None:
        session.ensure_required_tables()
        session.get_table("schedule").raw_df = raw_tables.get("schedule")
