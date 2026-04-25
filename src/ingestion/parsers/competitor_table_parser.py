from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.application.contracts import TableKey
from src.domain import Competitor
from .assignment_table_parser_base import AssignmentTableParserBase
from .errors import UserFacingParseError
from src.ingestion.services import AssignmentColumnsMode, AssignmentColumnsSelection


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

