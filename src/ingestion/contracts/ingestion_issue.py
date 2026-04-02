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
        ctx = IngestionIssue._freeze_for_hash(self.context)
        return (
            self.table_key,
            self.code,
            self.severity.value,
            self.row_index,
            self.column_key,
            self.message,
            ctx,
        )

    @staticmethod
    def _freeze_for_hash(value: Any) -> Any:
        if isinstance(value, dict):
            return tuple(
                (k, IngestionIssue._freeze_for_hash(v))
                for k, v in sorted(value.items(), key=lambda x: str(x[0]))
            )
        if isinstance(value, list):
            return tuple(IngestionIssue._freeze_for_hash(v) for v in value)
        if isinstance(value, set):
            return tuple(sorted(IngestionIssue._freeze_for_hash(v) for v in value))
        if isinstance(value, tuple):
            return tuple(IngestionIssue._freeze_for_hash(v) for v in value)
        return value
