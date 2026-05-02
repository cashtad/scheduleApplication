from __future__ import annotations

from src.application.contracts import all_table_keys
from src.ingestion import FullIngestionResult, IngestionSeverity
from src.session import AppSession

from .table_status_transition_service import TableStatusTransitionService


class SessionStatusSyncService:
    def __init__(self, transition_service: TableStatusTransitionService) -> None:
        self._transition_service = transition_service

    def sync_after_ingestion(
        self,
        session: AppSession,
        ingestion_result: FullIngestionResult,
    ) -> None:
        session.ensure_required_tables()

        schema_by_table: dict[str, list] = {}
        for issue in ingestion_result.schema_issues:
            schema_by_table.setdefault(issue.table_key, []).append(issue)

        for table_key in all_table_keys():
            table = session.get_table(table_key)
            issues = schema_by_table.get(table_key, [])

            error_codes = {
                i.code for i in issues if i.severity == IngestionSeverity.ERROR
            }
            warning_codes = {
                i.code for i in issues if i.severity == IngestionSeverity.WARNING
            }

            table.status = self._transition_service.on_ingestion_outcome(
                table=table,
                error_codes=error_codes,
                warning_codes=warning_codes,
            )
