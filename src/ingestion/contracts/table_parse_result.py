from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from .ingestion_issue import IngestionIssue
from .ingestion_severity import IngestionSeverity
from .table_parse_stats import TableParseStats

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class TableParseResult(Generic[T]):
    table_key: str
    items: list[T] = field(default_factory=list)
    issues: list[IngestionIssue] = field(default_factory=list)
    total_rows: int = 0
    parsed_rows: int = 0
    skipped_rows: int = 0

    @property
    def errors(self) -> list[IngestionIssue]:
        return [i for i in self.issues if i.severity == IngestionSeverity.ERROR]

    @property
    def warnings(self) -> list[IngestionIssue]:
        return [i for i in self.issues if i.severity == IngestionSeverity.WARNING]

    @property
    def stats(self) -> TableParseStats:
        return TableParseStats(
            table_key=self.table_key,
            total_rows=self.total_rows,
            parsed_rows=self.parsed_rows,
            skipped_rows=self.skipped_rows,
            error_count=len(self.errors),
            warning_count=len(self.warnings),
        )