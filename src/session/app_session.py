from __future__ import annotations

from dataclasses import dataclass, field

from src.application.contracts import required_table_keys

from .table_runtime_state import TableRuntimeState


SESSION_VERSION: int = 2

# TODO: поменять работу со стрингом на работу с TableKey
@dataclass(slots=True)
class AppSession:
    version: int = SESSION_VERSION
    tables: dict[str, TableRuntimeState] = field(default_factory=dict)
    saved_at: str | None = None  # ISO timestamp of last persisted snapshot

    def ensure_required_tables(self) -> None:
        for table_key in required_table_keys():
            self.tables.setdefault(table_key, TableRuntimeState(table_key=table_key))

    def get_table(self, table_key: str) -> TableRuntimeState:
        self.ensure_required_tables()
        return self.tables[table_key]

    def is_ready_to_analyze(self) -> bool:
        self.ensure_required_tables()
        return all(self.tables[k].is_ready() for k in required_table_keys())
