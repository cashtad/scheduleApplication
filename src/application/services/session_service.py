from __future__ import annotations

from typing import Iterable

from src.application.use_cases import SaveSessionUseCase
from src.session import AppSession
from src.application.contracts import TableKey


from .table_status_transition_service import TableStatusTransitionService


class SessionService:
    def __init__(
        self,
        save_session_use_case: SaveSessionUseCase,
        transition_service: TableStatusTransitionService,
    ) -> None:
        self._save_session_use_case = save_session_use_case
        self._transition_service = transition_service

    def set_file(self, session: AppSession, table_key: TableKey, file_path: str) -> None:
        table = session.get_table(table_key)
        table.file_path = file_path
        table.sheet_name = None
        table.column_mapping.clear()
        table.column_signature.clear()
        table.raw_df = None
        table.status = self._transition_service.on_file_selected(table)
        self._save_session_use_case.execute(session)

    def clear_table(self, session: AppSession, table_key: TableKey) -> None:
        table = session.get_table(table_key)
        table.file_path = None
        table.sheet_name = None
        table.column_mapping.clear()
        table.column_signature.clear()
        table.raw_df = None
        table.status = self._transition_service.on_file_selected(table)
        self._save_session_use_case.execute(session)

    def set_sheet(self, session: AppSession, table_key: TableKey, sheet_name: str) -> None:
        table = session.get_table(table_key)
        table.sheet_name = sheet_name
        table.column_mapping.clear()
        table.column_signature.clear()
        table.raw_df = None
        table.status = self._transition_service.on_sheet_selected(table)
        self._save_session_use_case.execute(session)

    def set_mapping(
        self,
        session: AppSession,
        table_key: TableKey,
        column_mapping: dict[str, str],
        current_columns: Iterable[str],
    ) -> None:
        table = session.get_table(table_key)
        table.column_mapping = dict(column_mapping)
        table.column_signature = [str(c) for c in current_columns]
        table.raw_df = None
        table.status = self._transition_service.on_mapping_applied(table)

        self._save_session_use_case.execute(session)

    def mark_ready(self, session: AppSession, table_key: TableKey) -> None:
        table = session.get_table(table_key)
        table.status = self._transition_service.on_mark_ready(table)
        self._save_session_use_case.execute(session)

    def mark_mapping_stale(self, session: AppSession, table_key: TableKey) -> None:
        table = session.get_table(table_key)
        table.status = self._transition_service.on_ingestion_outcome(
            table=table,
            error_codes=set(),
            warning_codes={"COLUMN_SIGNATURE_MISMATCH"},
        )
        self._save_session_use_case.execute(session)

    def mark_broken_sheet(self, session: AppSession, table_key: TableKey) -> None:
        table = session.get_table(table_key)
        table.status = self._transition_service.on_ingestion_outcome(
            table=table,
            error_codes={"SHEET_NOT_FOUND"},
            warning_codes=set(),
        )
        self._save_session_use_case.execute(session)