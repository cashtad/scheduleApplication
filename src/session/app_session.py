from __future__ import annotations

from dataclasses import dataclass, field

from .analysis_runtime_state import AnalysisRuntimeState
from .table_runtime_state import TableRuntimeState


REQUIRED_TABLE_KEYS: tuple[str, ...] = ("competitions", "competitors", "jury", "schedule")


@dataclass(slots=True)
class AppSession:
    version: int = 1
    tables: dict[str, TableRuntimeState] = field(default_factory=dict)
    analysis: AnalysisRuntimeState = field(default_factory=AnalysisRuntimeState)
    saved_at: str | None = None  # ISO timestamp of last persisted snapshot

    def ensure_required_tables(self) -> None:
        for table_key in REQUIRED_TABLE_KEYS:
            self.tables.setdefault(table_key, TableRuntimeState(table_key=table_key))

    def get_table(self, table_key: str) -> TableRuntimeState:
        self.ensure_required_tables()
        return self.tables[table_key]

    def is_ready_to_analyze(self) -> bool:
        self.ensure_required_tables()
        return all(self.tables[k].is_ready() for k in REQUIRED_TABLE_KEYS)