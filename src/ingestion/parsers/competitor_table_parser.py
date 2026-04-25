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

