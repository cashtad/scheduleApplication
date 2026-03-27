from __future__ import annotations

from dataclasses import dataclass, field

from ...domain import Competition, Competitor, JuryMember, Performance
from ...ingestion import IngestionIssue, TableParseStats, IngestionSeverity


@dataclass(frozen=True, slots=True)
class PrepareDataResult:
    competitions: list[Competition] = field(default_factory=list)
    competitors: list[Competitor] = field(default_factory=list)
    jury_members: list[JuryMember] = field(default_factory=list)
    performances: list[Performance] = field(default_factory=list)

    schema_issues: list[IngestionIssue] = field(default_factory=list)
    row_issues: list[IngestionIssue] = field(default_factory=list)
    table_stats: list[TableParseStats] = field(default_factory=list)

    @property
    def all_issues(self) -> list[IngestionIssue]:
        return self.schema_issues + self.row_issues

    @property
    def schema_errors(self) -> list[IngestionIssue]:
        return [i for i in self.schema_issues if i.severity == IngestionSeverity.ERROR]

    @property
    def schema_warnings(self) -> list[IngestionIssue]:
        return [i for i in self.schema_issues if i.severity == IngestionSeverity.WARNING]

    @property
    def row_errors(self) -> list[IngestionIssue]:
        return [i for i in self.row_issues if i.severity == IngestionSeverity.ERROR]

    @property
    def row_warnings(self) -> list[IngestionIssue]:
        return [i for i in self.row_issues if i.severity == IngestionSeverity.WARNING]

    @property
    def schema_errors_count(self) -> int:
        return len(self.schema_errors)

    @property
    def total_warnings_count(self) -> int:
        return len(self.schema_warnings) + len(self.row_warnings)

    @property
    def total_rows(self) -> int:
        return sum(s.total_rows for s in self.table_stats)

    @property
    def total_row_errors_count(self) -> int:
        return sum(s.error_count for s in self.table_stats)

    @property
    def row_error_rate(self) -> float:
        return 0.0 if self.total_rows == 0 else self.total_row_errors_count / self.total_rows
