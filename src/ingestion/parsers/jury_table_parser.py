from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pandas import DataFrame

from src.application.contracts import TableKey
from src.domain import JuryMember
from .assignment_table_parser_base import AssignmentTableParserBase
from src.ingestion.services import AssignmentColumnsMode, AssignmentColumnsSelection
from src.ingestion.dto import IngestionSeverity, TableParseResult, IngestionIssue



@dataclass(frozen=True, slots=True)
class JuryParserConfig:
    assignment_mode: AssignmentColumnsMode = AssignmentColumnsMode.PREFIX
    assigned_markers: frozenset[str] = frozenset({"1"})


class JuryTableParser(AssignmentTableParserBase[JuryMember]):
    def __init__(
        self,
        mapping: dict[str, str],
        config: JuryParserConfig | None = None,
    ) -> None:
        super().__init__(table_key=TableKey.JURY, mapping=mapping)
        self._config = config or JuryParserConfig()

    @property
    def assignment_mode(self) -> AssignmentColumnsMode:
        return self._config.assignment_mode

    @property
    def assigned_markers(self) -> frozenset[str]:
        return self._config.assigned_markers

    @property
    def row_parse_error_code(self) -> str:
        return "JURY_ROW_PARSE_FAILED"

    @property
    def row_parse_error_message(self) -> str:
        return "Nepodařilo se zpracovat řádek poroty. Zkontrolujte hodnoty ve sloupcích."

    def parse(self, df: DataFrame) -> TableParseResult[JuryMember]:
        issues: list[IngestionIssue] = []
        items: list[JuryMember] = []

        total_rows = len(df.index)
        parsed_rows = 0

        try:
            assignment_selection = self._select_assignment_columns(df)
        except Exception as exc:
            issues.append(
                self.make_issue_from_exception(
                    exc=exc,
                    default_code="ASSIGNMENT_COLUMNS_NOT_FOUND",
                    default_message="Nepodařilo se určit sloupce přiřazení soutěží. Zkontrolujte mapování prefixu nebo názvy sloupců.",
                    severity=self._error_severity(),
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
                if parsed is None:
                    issues.append(
                        self.make_row_warning(
                            row_index=safe_row_index,
                            code="JURY_ROW_EMPTY_NAME/SURNAME",
                            message="Řádek byl přeskočen, protože jméno nebo příjmení je prázdné",
                        )
                    )
                    continue
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
        self, row: Any, assignment_selection: AssignmentColumnsSelection
    ) -> JuryMember | None:
        fullname = self._extract_fullname(row)
        if not fullname:
            return None

        competition_ids = self._extract_assignments(
            row=row, assignment_selection=assignment_selection
        )

        return JuryMember(
            fullname=fullname,
            competition_ids=competition_ids,
        )

    def _extract_fullname(self, row: Any) -> str:
        fullname_col = (self.mapping.get("fullname") or "").strip()
        if fullname_col:
            fullname = self.as_str(row[fullname_col])
            return fullname

        name_col = (self.mapping.get("name") or "").strip()
        surname_col = (self.mapping.get("surname") or "").strip()
        name = self.as_str(row[name_col])
        surname = self.as_str(row[surname_col])
        full = f"{name} {surname}".strip()
        return full


