from __future__ import annotations

from dataclasses import dataclass

from src.application.contracts import TABLE_MAPPING_SCHEMAS
from src.session import TableRuntimeState


@dataclass(frozen=True, slots=True)
class MappingValidationResult:
    is_valid: bool
    message: str = ""


class MappingTemplateService:
    def get_applicable_saved_mapping(
        self,
        table_state: TableRuntimeState,
        current_columns: list[str],
    ) -> dict[str, str] | None:
        if not table_state.column_mapping:
            return None

        result = self.validate_mapping(
            table_key=table_state.table_key,
            mapping=table_state.column_mapping,
            current_columns=current_columns,
        )
        if not result.is_valid:
            return None
        return dict(table_state.column_mapping)

    def validate_mapping(
        self,
        table_key: str,
        mapping: dict[str, str],
        current_columns: list[str],
    ) -> MappingValidationResult:
        schema = TABLE_MAPPING_SCHEMAS[table_key]
        existing = set(current_columns)

        for field in schema.fields:
            value = (mapping.get(field.key) or "").strip()
            if field.required and not value:
                return MappingValidationResult(
                    False, f"Povinné pole '{field.label}' není vyplněno."
                )

        for field in schema.fields:
            if field.virtual:
                continue
            value = (mapping.get(field.key) or "").strip()
            if value and value not in existing:
                return MappingValidationResult(
                    False,
                    f"Vybraný sloupec '{value}' pro pole '{field.label}' neexistuje v tabulce.",
                )

        if table_key in {"competitors", "jury"}:
            prefix = (mapping.get("assignment_prefix") or "").strip()
            if prefix:
                matched = [c for c in current_columns if str(c).startswith(prefix)]
                if not matched:
                    return MappingValidationResult(
                        False, f"Prefix '{prefix}' neodpovídá žádnému sloupci."
                    )
            else:
                numeric = [c for c in current_columns if str(c).strip().isdigit()]
                if not numeric:
                    return MappingValidationResult(
                        False,
                        "Pro prázdný prefix nebyly nalezeny číselné sloupce přiřazení.",
                    )

        if table_key == "jury":
            fullname = (mapping.get("fullname") or "").strip()
            name = (mapping.get("name") or "").strip()
            surname = (mapping.get("surname") or "").strip()
            if not fullname and not (name and surname):
                return MappingValidationResult(
                    False,
                    "Pro porotu je potřeba buď 'Celé jméno', nebo kombinace 'Jméno' + 'Příjmení'.",
                )

        return MappingValidationResult(True, "")
