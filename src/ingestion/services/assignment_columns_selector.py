from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class AssignmentColumnsMode(Enum):
    PREFIX = "prefix"
    NUMERIC_HEADERS = "numeric_headers"


@dataclass(frozen=True, slots=True)
class AssignmentColumnsSelection:
    mode: AssignmentColumnsMode
    columns: list[str]
    prefix: str | None = None


class AssignmentColumnsSelector:
    @staticmethod
    def select(
        available_columns: Iterable[str],
        mode: AssignmentColumnsMode,
        prefix: str | None = None,
    ) -> AssignmentColumnsSelection:

        if mode == AssignmentColumnsMode.PREFIX:
            normalized_prefix = (prefix or "").strip()
            if not normalized_prefix:
                raise ValueError("Režim prefixu vyžaduje neprázdný prefix")
            selected = [
                c for c in available_columns if str(c).startswith(normalized_prefix)
            ]
            if not selected:
                raise ValueError(
                    f"Nebyly nalezeny žádné sloupce s prefixem '{normalized_prefix}'"
                )
            return AssignmentColumnsSelection(
                mode=mode,
                columns=selected,
                prefix=normalized_prefix,
            )

        if mode == AssignmentColumnsMode.NUMERIC_HEADERS:
            selected = [c for c in available_columns if str(c).strip().isdigit()]
            if not selected:
                raise ValueError("Nebyly nalezeny sloupce přiřazení s číselným záhlavím")
            return AssignmentColumnsSelection(
                mode=mode,
                columns=selected,
                prefix=None,
            )

        raise ValueError(f"Nepodporovaný režim sloupců přiřazení: {mode}")
