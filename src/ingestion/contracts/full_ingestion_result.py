from __future__ import annotations

from dataclasses import dataclass, field

from ...domain import Competition, Competitor, JuryMember, Performance
from .ingestion_issue import IngestionIssue
from .table_parse_result import TableParseResult
from .table_parse_stats import TableParseStats


@dataclass(frozen=True, slots=True)
class FullIngestionResult:
    competitions: TableParseResult[Competition]
    competitors: TableParseResult[Competitor]
    jury_members: TableParseResult[JuryMember]
    performances: TableParseResult[Performance]
    schema_issues: list[IngestionIssue] = field(default_factory=list)

    @property
    def all_row_issues(self) -> list[IngestionIssue]:
        return (
            self.competitions.issues
            + self.competitors.issues
            + self.jury_members.issues
            + self.performances.issues
        )

    @property
    def all_issues(self) -> list[IngestionIssue]:
        return self.schema_issues + self.all_row_issues

    @property
    def table_stats(self) -> list[TableParseStats]:
        return [
            self.competitions.stats,
            self.competitors.stats,
            self.jury_members.stats,
            self.performances.stats,
        ]

    @property
    def total_rows(self) -> int:
        return sum(s.total_rows for s in self.table_stats)

    @property
    def total_row_errors(self) -> int:
        return sum(s.error_count for s in self.table_stats)

    @property
    def row_error_rate(self) -> float:
        return 0.0 if self.total_rows == 0 else self.total_row_errors / self.total_rows