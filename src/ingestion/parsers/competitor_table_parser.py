from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pandas import DataFrame

from src.domain import Competitor
from .base_table_parser import BaseTableParser
from .errors import UserFacingParseError
from src.ingestion.contracts import IngestionIssue, TableParseResult
from src.ingestion.services import (
    AssignmentColumnsMode,
    AssignmentColumnsSelection,
    AssignmentColumnsSelector,
)


@dataclass(frozen=True, slots=True)
class CompetitorParserConfig:
    assignment_mode: AssignmentColumnsMode = AssignmentColumnsMode.PREFIX
    assigned_markers: frozenset[str] = frozenset({"1"})  # can be extended later
    treat_unassigned_as_empty: bool = True


class CompetitorTableParser(BaseTableParser[Competitor]):
    def __init__(
        self,
        mapping: dict[str, str],
        config: CompetitorParserConfig | None = None,
    ) -> None:
        super().__init__(table_key="competitors", mapping=mapping)
        self._config = config or CompetitorParserConfig()

    def required_mapping_keys(self) -> list[str]:
        base = ["count", "p1_name_surname", "p2_name_surname"]
        if self._config.assignment_mode == AssignmentColumnsMode.PREFIX:
            base.append("assignment_prefix")
        return base

    def virtual_mapping_keys(self) -> set[str]:
        # assignment_prefix is not a dataframe column reference, but parser configuration value
        return {"assignment_prefix"}

    def parse(self, df: DataFrame) -> TableParseResult[Competitor]:
        self.validate_mapping_columns(df)

        issues: list[IngestionIssue] = []
        items: list[Competitor] = []

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
            safe_row_index = self.as_row_index(row_index)
            try:
                competitor = self._parse_row(
                    row=row,
                    assignment_selection=assignment_selection,
                )
                items.append(competitor)
                parsed_rows += 1

            except Exception as exc:
                issues.append(
                    self.make_row_error_from_exception(
                        row_index=safe_row_index,
                        exc=exc,
                        default_code="COMPETITOR_ROW_PARSE_FAILED",
                        default_message="Nepodařilo se zpracovat řádek soutěžícího. Zkontrolujte hodnoty ve sloupcích.",
                        context={"row_index": safe_row_index},
                    )
                )

        return self.build_result(
            items=items,
            issues=issues,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
        )

    # --------------------------
    # Internal parsing
    # --------------------------

    def _parse_row(
        self,
        row: Any,
        assignment_selection: AssignmentColumnsSelection,
    ) -> Competitor:
        count_raw = row[self.mapping["count"]]
        p1_raw = row[self.mapping["p1_name_surname"]]
        p2_raw = row[self.mapping["p2_name_surname"]]

        count = self._parse_count_or_raise(count_raw)
        dancer_1_name = self.as_str(p1_raw)
        dancer_2_name = self._parse_second_name(count=count, raw_value=p2_raw)

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

    def _parse_count_or_raise(self, raw_value: Any) -> int:
        if self.is_empty(raw_value):
            raise UserFacingParseError(
                code="COUNT_EMPTY",
                message="Pole 'count' je prázdné",
                column_key="count",
            )

        count_text = self.as_str(raw_value)
        if count_text not in {"1", "2"}:
            raise UserFacingParseError(
                code="COUNT_INVALID",
                message=f"Pole 'count' musí být 1 nebo 2, ale je '{count_text}'",
                column_key="count",
                context={"value": count_text},
            )

        return int(count_text)

    def _parse_second_name(self, count: int, raw_value: Any) -> str | None:
        if count == 1:
            # enforce None for solo entries
            return None

        value = self.as_str(raw_value)
        if not value:
            raise UserFacingParseError(
                code="SECOND_NAME_REQUIRED",
                message="Pole 'p2_name_surname' je povinné, když count=2",
                column_key="p2_name_surname",
            )
        return value

    def _select_assignment_columns(self, df: DataFrame) -> AssignmentColumnsSelection:
        prefix = self.mapping.get("assignment_prefix", "")
        if prefix.strip() == "":
            mode = AssignmentColumnsMode.NUMERIC_HEADERS
        else:
            mode = AssignmentColumnsMode.PREFIX
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

            competition_id = CompetitorTableParser._competition_id_from_column(
                column_name=column_name,
                assignment_selection=assignment_selection,
            )
            competition_ids.add(competition_id)

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

        # PREFIX mode
        assert assignment_selection.prefix is not None  # guaranteed by selector
        remainder = column_name.removeprefix(assignment_selection.prefix).strip()
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
        return normalized in {m.lower() for m in self._config.assigned_markers}

    @staticmethod
    def _error_severity():
        from src.ingestion.contracts.ingestion_severity import IngestionSeverity

        return IngestionSeverity.ERROR
