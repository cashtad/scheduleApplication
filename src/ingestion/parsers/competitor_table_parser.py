from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pandas import DataFrame

from src.application.contracts import TableKey
from src.domain import Competitor
from .assignment_table_parser_base import AssignmentTableParserBase
from src.ingestion.services import AssignmentColumnsMode, AssignmentColumnsSelection
from src.ingestion.dto import IngestionSeverity, TableParseResult, IngestionIssue

@dataclass(frozen=True, slots=True)
class CompetitorParserConfig:
    assignment_mode: AssignmentColumnsMode = AssignmentColumnsMode.PREFIX
    assigned_markers: frozenset[str] = frozenset({"1"})  # can be extended later
    treat_unassigned_as_empty: bool = True


class CompetitorTableParser(AssignmentTableParserBase[Competitor]):
    def __init__(
        self,
        mapping: dict[str, str],
        config: CompetitorParserConfig | None = None,
    ) -> None:
        super().__init__(table_key=TableKey.COMPETITORS, mapping=mapping)
        self._config = config or CompetitorParserConfig()

    @property
    def assignment_mode(self) -> AssignmentColumnsMode:
        return self._config.assignment_mode

    @property
    def assigned_markers(self) -> frozenset[str]:
        return self._config.assigned_markers

    @property
    def row_parse_error_code(self) -> str:
        return "COMPETITOR_ROW_PARSE_FAILED"

    @property
    def row_parse_error_message(self) -> str:
        return "Nepodařilo se zpracovat řádek soutěžícího. Zkontrolujte hodnoty ve sloupcích."

    def _row_error_context(self, row_index: int) -> dict[str, Any] | None:
        return {"row_index": row_index}

    def parse(self, df: DataFrame) -> TableParseResult[Competitor]:
        issues: list[IngestionIssue] = []
        items: list[Competitor] = []

        total_rows = len(df.index)
        parsed_rows = 0

        try:
            assignment_selection = self._select_assignment_columns(df)
        except Exception as exc:
            #TODO: check
            issues.append(
                self.make_issue_from_exception(
                    exc=exc,
                    default_code="ASSIGNMENT_COLUMNS_NOT_FOUND",
                    default_message="Nepodařilo se určit sloupce přiřazení soutěží. Zkontrolujte mapování prefixu nebo názvy sloupců.",
                    severity=IngestionSeverity.WARNING,
                    context={
                        "assignment_mode": self.assignment_mode.value,
                        "assignment_prefix": self.mapping.get("assignment_prefix"),
                    },
                )
            )
            return self.build_result(
                items=items,
                issues=issues,
                total_rows=total_rows,
                parsed_rows=parsed_rows,
            )

        for row_index, row in df.iterrows():
            safe_row_index = self.as_row_index(row_index)
            try:
                parsed = self._parse_row(row=row, assignment_selection=assignment_selection)
                items.append(parsed)
                parsed_rows += 1
            except Exception as exc:
                issues.append(
                    self.make_row_error_from_exception(
                        row_index=safe_row_index,
                        exc=exc,
                        default_code=self.row_parse_error_code,
                        default_message=self.row_parse_error_message,
                        context=self._row_error_context(safe_row_index),
                    )
                )

        return self.build_result(
            items=items,
            issues=issues,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
        )

    def _parse_row(
        self,
        row: Any,
        assignment_selection: AssignmentColumnsSelection,
    ) -> Competitor:
        p1_raw = row[self.mapping["p1_name_surname"]]
        p2_raw = row[self.mapping["p2_name_surname"]]

        dancer_1_name = self.as_str(p1_raw)
        dancer_2_name = self._parse_second_name(raw_value=p2_raw)

        count = 2 if dancer_2_name else 1

        competition_ids = self._extract_assignments(
            row=row,
            assignment_selection=assignment_selection,
        )

        return Competitor(
            participants_per_entry=count,
            dancer_1_name=dancer_1_name,
            dancer_2_name=dancer_2_name,
            competition_ids=competition_ids,
        )

    def _parse_second_name(self, raw_value: Any) -> str | None:
        value = self.as_str(raw_value)
        return value

