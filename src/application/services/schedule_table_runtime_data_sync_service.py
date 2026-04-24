from __future__ import annotations

from pandas import DataFrame

from src.application.contracts import TableKey
from src.session import AppSession


class ScheduleTableRuntimeDataSyncService:
    @staticmethod
    def sync_raw_tables(
        session: AppSession,
        raw_tables: dict[str, DataFrame | None],
    ) -> None:
        session.ensure_required_tables()
        schedule_key = TableKey.SCHEDULE.value
        session.get_table(schedule_key).raw_df = raw_tables.get(schedule_key)
