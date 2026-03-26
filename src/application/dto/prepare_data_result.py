from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TableParseStats:
    table_key: str
    total_rows: int = 0
    parsed_rows: int = 0
    row_errors: int = 0
    row_warnings: int = 0


@dataclass(frozen=True, slots=True)
class PrepareDataResult:
    # Parsed domain entities
    competitions: list[Any] = field(default_factory=list)
    competitors: list[Any] = field(default_factory=list)
    jury_members: list[Any] = field(default_factory=list)
    performances: list[Any] = field(default_factory=list)

    # Parsing quality
    schema_errors: list[str] = field(default_factory=list)
    schema_warnings: list[str] = field(default_factory=list)
    row_errors: list[str] = field(default_factory=list)
    row_warnings: list[str] = field(default_factory=list)
    table_stats: list[TableParseStats] = field(default_factory=list)

    @property
    def total_rows(self) -> int:
        return sum(s.total_rows for s in self.table_stats)

    @property
    def total_row_errors_count(self) -> int:
        return sum(s.row_errors for s in self.table_stats)

    @property
    def row_error_rate(self) -> float:
        return 0.0 if self.total_rows == 0 else self.total_row_errors_count / self.total_rows

    @property
    def schema_errors_count(self) -> int:
        return len(self.schema_errors)

    @property
    def total_warnings_count(self) -> int:
        return len(self.schema_warnings) + len(self.row_warnings)