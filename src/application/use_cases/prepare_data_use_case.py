from __future__ import annotations

from ..dto.prepare_data_result import PrepareDataResult


class PrepareDataUseCase:
    """
    Reads source tables from session, applies mapping, runs schema+row parsing,
    and returns domain entities + parsing quality summary.
    """

    def __init__(self, table_ingestion_service) -> None:
        self._table_ingestion_service = table_ingestion_service

    def execute(self, session) -> PrepareDataResult:
        # TODO (next step):
        # return self._table_ingestion_service.ingest(session)
        raise NotImplementedError