from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class TableStatus(Enum):
    EMPTY = "empty"
    FILE_SELECTED = "file_selected"
    SHEET_SELECTED = "sheet_selected"
    MAPPED = "mapped"
    READY = "ready"
    BROKEN_PATH = "broken_path"
    BROKEN_SHEET = "broken_sheet"
    MAPPING_STALE = "mapping_stale"

@dataclass(slots=True)
class TableRuntimeState:
    table_key: str #TODO: поменять на работу с TableKey
    file_path: str | None = None
    sheet_name: str | None = None
    column_mapping: dict[str, str] = field(default_factory=dict)
    column_signature: list[str] = field(default_factory=list)
    status: TableStatus = TableStatus.EMPTY
    raw_df: Any | None = None

    def is_minimally_configured(self) -> bool:
        return bool(self.file_path and self.sheet_name and self.column_mapping)

    def is_ready(self) -> bool:
        return self.status == TableStatus.READY