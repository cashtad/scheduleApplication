from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .table_status import TableStatus


@dataclass(slots=True)
class TableRuntimeState:
    table_key: str
    file_path: str | None = None
    sheet_name: str | None = None
    column_mapping: dict[str, str] = field(default_factory=dict)
    column_signature: list[str] = field(default_factory=list)
    status: TableStatus = TableStatus.EMPTY
    raw_df: Any | None = None  # runtime only

    def is_minimally_configured(self) -> bool:
        return bool(self.file_path and self.sheet_name and self.column_mapping)

    def is_ready(self) -> bool:
        return self.status == TableStatus.READY