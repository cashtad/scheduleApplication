from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PersistedTableState:
    file_path: str | None
    sheet_name: str | None
    column_mapping: dict[str, str]
    column_signature: list[str]


@dataclass(frozen=True, slots=True)
class PersistedSession:
    version: int
    saved_at: str | None
    tables: dict[str, PersistedTableState]


class SessionStore(Protocol):
    def load(self) -> PersistedSession | None:
        ...

    def save(self, session: PersistedSession) -> None:
        ...