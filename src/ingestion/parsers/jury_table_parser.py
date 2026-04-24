from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain import JuryMember
from .assignment_table_parser_base import AssignmentTableParserBase
from .errors import UserFacingParseError
from src.ingestion.services import AssignmentColumnsMode, AssignmentColumnsSelection


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
        super().__init__(table_key="jury", mapping=mapping)
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


    def _parse_row(
        self, row: Any, assignment_selection: AssignmentColumnsSelection
    ) -> JuryMember:
        fullname = self._extract_fullname(row)

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
            if not fullname:
                raise UserFacingParseError(
                    code="JURY_FULLNAME_EMPTY",
                    message="Pole 'fullname' je prázdné",
                    column_key="fullname",
                )
            return fullname

        name_col = (self.mapping.get("name") or "").strip()
        surname_col = (self.mapping.get("surname") or "").strip()
        name = self.as_str(row[name_col])
        surname = self.as_str(row[surname_col])
        full = f"{name} {surname}".strip()
        if not full:
            raise UserFacingParseError(
                code="JURY_NAME_SURNAME_EMPTY",
                message="Pole 'name'/'surname' jsou prázdná",
                context={"name": name_col, "surname": surname_col},
            )
        return full


