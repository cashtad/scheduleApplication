from __future__ import annotations

from dataclasses import dataclass

from src.application.contracts import TableKey


@dataclass(frozen=True, slots=True)
class TableParseStats:
    table_key: TableKey
    total_rows: int
    parsed_rows: int
    skipped_rows: int
    error_count: int
    warning_count: int