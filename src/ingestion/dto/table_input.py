from __future__ import annotations

from dataclasses import dataclass

from application.contracts import TableKey


@dataclass(frozen=True, slots=True)
class TableInput: # TODO: duplicates table_runtime_state's class
    table_key: TableKey
    file_path: str
    sheet_name: str | None
    mapping: dict[str, str]
    column_signature: list[str]