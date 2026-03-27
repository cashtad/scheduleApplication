from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pandas import DataFrame

from ...domain import JuryMember
from ..contracts import IngestionIssue, TableParseResult
from .base_table_parser import BaseTableParser
from ..services import (
    AssignmentColumnsMode,
    AssignmentColumnsSelection,
    AssignmentColumnsSelector,
)


@dataclass(frozen=True, slots=True)
class JuryParserConfig:
    assignment_mode: AssignmentColumnsMode = AssignmentColumnsMode.PREFIX
    assigned_markers: frozenset[str] = frozenset({"1"})


class JuryTableParser(BaseTableParser[JuryMember]):
    def __init__(self, mapping: dict[str, str], config: JuryParserConfig | None = None) -> None:
        super().__init__(table_key="jury", mapping=mapping)
        self._config = config or JuryParserConfig()

    def required_mapping_keys(self) -> list[str]:
        base = ["fullname"]
        if self._config.assignment_mode == AssignmentColumnsMode.PREFIX:
            base.append("assignment_prefix")
        return base

    def virtual_mapping_keys(self) -> set[str]:
        return {"assignment_prefix"}

    def parse(self, df: DataFrame) -> TableParseResult[JuryMember]:
        self.validate_mapping_columns(df)

        issues: list[IngestionIssue] = []
        items: list[JuryMember] = []
        total_rows = len(df.index)
        parsed_rows = 0

        try:
            assignment_selection = self._select_assignment_columns(df)
        except Exception as exc:
            issues.append(
                self.make_issue(
                    code="ASSIGNMENT_COLUMNS_NOT_FOUND",
                    message=str(exc),
                    severity=self._error_severity(),
                    context={
                        "assignment_mode": self._config.assignment_mode.value,
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
            try:
                member = self._parse_row(row, assignment_selection=assignment_selection)
                items.append(member)
                parsed_rows += 1
            except Exception as exc:
                issues.append(
                    self.make_row_error(
                        row_index=int(row_index),
                        code="JURY_ROW_PARSE_FAILED",
                        message=f"Failed to parse jury row: {exc}",
                    )
                )

        return self.build_result(
            items=items,
            issues=issues,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
        )

    def _parse_row(self, row: Any, assignment_selection: AssignmentColumnsSelection) -> JuryMember:
        fullname = self.as_str(row[self.mapping["fullname"]])
        competition_ids = self._extract_assignments(row=row, assignment_selection=assignment_selection)

        return JuryMember(
            fullname=fullname,
            competition_ids=competition_ids,
        )

    def _select_assignment_columns(self, df: DataFrame) -> AssignmentColumnsSelection:
        prefix = self.mapping.get("assignment_prefix")
        return AssignmentColumnsSelector.select(
            available_columns=[str(c) for c in df.columns],
            mode=self._config.assignment_mode,
            prefix=prefix,
        )

    def _extract_assignments(self, row: Any, assignment_selection: AssignmentColumnsSelection) -> frozenset[int]:
        competition_ids: set[int] = set()
        for column_name in assignment_selection.columns:
            if not self._is_assigned(row[column_name]):
                continue
            competition_ids.add(JuryTableParser._competition_id_from_column(column_name, assignment_selection))
        return frozenset(competition_ids)

    @staticmethod
    def _competition_id_from_column(
        column_name: str,
        assignment_selection: AssignmentColumnsSelection,
    ) -> int:
        if assignment_selection.mode == AssignmentColumnsMode.NUMERIC_HEADERS:
            txt = column_name.strip()
            if not txt.isdigit():
                raise ValueError(f"Assignment column '{column_name}' is not numeric")
            return int(txt)

        assert assignment_selection.prefix is not None
        remainder = column_name.removeprefix(assignment_selection.prefix).strip()
        if not remainder.isdigit():
            raise ValueError(
                f"Assignment column '{column_name}' does not contain numeric competition id "
                f"after prefix '{assignment_selection.prefix}'"
            )
        return int(remainder)

    def _is_assigned(self, value: Any) -> bool:
        normalized = self.as_str(value).lower()
        return normalized in {m.lower() for m in self._config.assigned_markers}

    @staticmethod
    def _error_severity():
        from ..contracts.ingestion_severity import IngestionSeverity

        return IngestionSeverity.ERROR