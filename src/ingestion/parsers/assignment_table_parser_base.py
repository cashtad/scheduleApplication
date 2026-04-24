from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pandas import DataFrame

from src.ingestion.dto import IngestionIssue, TableParseResult
from src.ingestion.services import (
    AssignmentColumnsMode,
    AssignmentColumnsSelection,
    AssignmentColumnsSelector,
)
from .base_table_parser import BaseTableParser
from .errors import UserFacingParseError

T = TypeVar("T")


class AssignmentTableParserBase(BaseTableParser[T], ABC, Generic[T]):
    def parse(self, df: DataFrame) -> TableParseResult[T]:
        issues: list[IngestionIssue] = []
        items: list[T] = []

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

    @property
    @abstractmethod
    def assignment_mode(self) -> AssignmentColumnsMode: ...

    @property
    @abstractmethod
    def assigned_markers(self) -> frozenset[str]: ...

    @property
    @abstractmethod
    def row_parse_error_code(self) -> str: ...

    @property
    @abstractmethod
    def row_parse_error_message(self) -> str: ...

    @abstractmethod
    def _parse_row(self, row: Any, assignment_selection: AssignmentColumnsSelection) -> T: ...

    def _row_error_context(self, row_index: int) -> dict[str, Any] | None:
        return None

    def _select_assignment_columns(self, df: DataFrame) -> AssignmentColumnsSelection:
        prefix = self.mapping.get("assignment_prefix", "")
        mode = self.assignment_mode
        if mode == AssignmentColumnsMode.PREFIX and prefix.strip() == "":
            mode = AssignmentColumnsMode.NUMERIC_HEADERS
        return AssignmentColumnsSelector.select(
            available_columns=df.columns,
            mode=mode,
            prefix=prefix,
        )

    def _extract_assignments(
        self,
        row: Any,
        assignment_selection: AssignmentColumnsSelection,
    ) -> frozenset[int]:
        competition_ids: set[int] = set()

        for column_name in assignment_selection.columns:
            cell_value = row[column_name]
            if not self._is_assigned(cell_value):
                continue

            competition_ids.add(
                AssignmentTableParserBase._competition_id_from_column(
                    column_name=column_name,
                    assignment_selection=assignment_selection,
                )
            )

        return frozenset(competition_ids)

    @staticmethod
    def _competition_id_from_column(
        column_name: str,
        assignment_selection: AssignmentColumnsSelection,
    ) -> int:
        if assignment_selection.mode == AssignmentColumnsMode.NUMERIC_HEADERS:
            text = str(column_name).strip()
            if not text.isdigit():
                raise UserFacingParseError(
                    code="ASSIGNMENT_COLUMN_NOT_NUMERIC",
                    message=f"Sloupec přiřazení '{column_name}' není číselný",
                    context={"column_name": column_name},
                )
            return int(text)

        assert assignment_selection.prefix is not None
        remainder = str(column_name).removeprefix(assignment_selection.prefix).strip()
        if not remainder.isdigit():
            raise UserFacingParseError(
                code="ASSIGNMENT_COLUMN_ID_INVALID",
                message=(
                    f"Sloupec přiřazení '{column_name}' neobsahuje číselné ID soutěže "
                    f"za prefixem '{assignment_selection.prefix}'"
                ),
                context={
                    "column_name": column_name,
                    "prefix": assignment_selection.prefix,
                },
            )
        return int(remainder)

    def _is_assigned(self, value: Any) -> bool:
        normalized = self.as_str(value).lower()
        return normalized in {marker.lower() for marker in self.assigned_markers}

