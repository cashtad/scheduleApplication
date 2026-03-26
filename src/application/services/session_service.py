from __future__ import annotations

from typing import Iterable

from ..use_cases.save_session_use_case import SaveSessionUseCase
from ...session.app_session import AppSession
from ...session.table_status import TableStatus


class SessionService:
    def __init__(self, save_session_use_case: SaveSessionUseCase) -> None:
        self._save_session_use_case = save_session_use_case

    def set_file(self, session: AppSession, table_key: str, file_path: str) -> None:
        table = session.get_table(table_key)
        table.file_path = file_path
        table.sheet_name = None
        table.column_mapping.clear()
        table.column_signature.clear()
        table.raw_df = None
        table.status = TableStatus.FILE_SELECTED
        session.analysis.is_stale = True
        self._save_session_use_case.execute(session)

    def set_sheet(self, session: AppSession, table_key: str, sheet_name: str) -> None:
        table = session.get_table(table_key)
        table.sheet_name = sheet_name
        table.column_mapping.clear()
        table.column_signature.clear()
        table.raw_df = None
        table.status = TableStatus.SHEET_SELECTED
        session.analysis.is_stale = True
        self._save_session_use_case.execute(session)

    def set_mapping(
        self,
        session: AppSession,
        table_key: str,
        column_mapping: dict[str, str],
        current_columns: Iterable[str],
    ) -> None:
        table = session.get_table(table_key)
        table.column_mapping = dict(column_mapping)
        table.column_signature = [str(c) for c in current_columns]
        table.raw_df = None

        table.status = TableStatus.MAPPED

        session.analysis.is_stale = True
        self._save_session_use_case.execute(session)

    def mark_ready(self, session: AppSession, table_key: str) -> None:
        table = session.get_table(table_key)
        table.status = TableStatus.READY
        self._save_session_use_case.execute(session)

    def mark_mapping_stale(self, session: AppSession, table_key: str) -> None:
        table = session.get_table(table_key)
        table.status = TableStatus.MAPPING_STALE
        session.analysis.is_stale = True
        self._save_session_use_case.execute(session)

    def mark_broken_sheet(self, session: AppSession, table_key: str) -> None:
        table = session.get_table(table_key)
        table.status = TableStatus.BROKEN_SHEET
        session.analysis.is_stale = True
        self._save_session_use_case.execute(session)