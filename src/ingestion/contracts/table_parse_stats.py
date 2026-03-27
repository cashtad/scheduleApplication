from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TableParseStats:
    table_key: str
    total_rows: int
    parsed_rows: int
    skipped_rows: int
    error_count: int
    warning_count: int