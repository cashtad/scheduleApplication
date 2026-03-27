from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ingestion_severity import IngestionSeverity


@dataclass(frozen=True, slots=True)
class IngestionIssue:
    table_key: str
    code: str
    message: str
    severity: IngestionSeverity
    row_index: int | None = None
    column_key: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def dedup_key(self) -> tuple:
        ctx = tuple(sorted(self.context.items(), key=lambda x: x[0]))
        return (
            self.table_key,
            self.code,
            self.severity.value,
            self.row_index,
            self.column_key,
            self.message,
            ctx,
        )