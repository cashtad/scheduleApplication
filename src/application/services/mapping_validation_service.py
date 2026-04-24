from __future__ import annotations

from dataclasses import dataclass

from src.application.contracts import TableKey, get_table_spec
from src.session import TableRuntimeState


@dataclass(frozen=True, slots=True)
class MappingValidationResult:
    is_valid: bool
    message: str = ""
    code: str | None = None
    field_key: str | None = None


class MappingValidationService:
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
        spec = get_table_spec(table_key)
        schema = spec.mapping_schema
        existing = set(current_columns)

        for field in schema.fields:
            value = (mapping.get(field.key) or "").strip()
            if field.required and not value:
                return MappingValidationResult(
                    is_valid=False,
                    message=f"Povinné pole '{field.label}' není vyplněno.",
                    code="MAP_REQUIRED_MISSING",
                    field_key=field.key,
                )

        for field in schema.fields:
            if field.virtual:
                continue
            value = (mapping.get(field.key) or "").strip()
            if value and value not in existing:
                return MappingValidationResult(
                    is_valid=False,
                    message=f"Vybraný sloupec '{value}' pro pole '{field.label}' neexistuje v tabulce.",
                    code="MAP_COLUMN_NOT_FOUND",
                    field_key=field.key,
                )

        assignment_check = self._validate_assignment_prefix(
            uses_assignment_columns=spec.uses_assignment_columns,
            mapping=mapping,
            current_columns=current_columns,
        )
        if assignment_check is not None:
            return assignment_check

        jury_check = self._validate_jury_name_shape(table_key=spec.key, mapping=mapping)
        if jury_check is not None:
            return jury_check

        return MappingValidationResult(is_valid=True)

    @staticmethod
    def _validate_assignment_prefix(
        uses_assignment_columns: bool,
        mapping: dict[str, str],
        current_columns: list[str],
    ) -> MappingValidationResult | None:
        if not uses_assignment_columns:
            return None

        prefix = (mapping.get("assignment_prefix") or "").strip()
        if prefix:
            matched = [c for c in current_columns if str(c).startswith(prefix)]
            if not matched:
                return MappingValidationResult(
                    is_valid=False,
                    message=f"Prefix '{prefix}' neodpovídá žádnému sloupci.",
                    code="ASSIGNMENT_PREFIX_NO_MATCH",
                    field_key="assignment_prefix",
                )
            return None

        numeric = [c for c in current_columns if str(c).strip().isdigit()]
        if not numeric:
            return MappingValidationResult(
                is_valid=False,
                message="Pro prázdný prefix nebyly nalezeny číselné sloupce přiřazení.",
                code="ASSIGNMENT_NUMERIC_COLUMNS_MISSING",
                field_key="assignment_prefix",
            )
        return None

    @staticmethod
    def _validate_jury_name_shape(
        table_key: TableKey,
        mapping: dict[str, str],
    ) -> MappingValidationResult | None:
        if table_key != TableKey.JURY:
            return None

        fullname = (mapping.get("fullname") or "").strip()
        name = (mapping.get("name") or "").strip()
        surname = (mapping.get("surname") or "").strip()
        if fullname or (name and surname):
            return None

        return MappingValidationResult(
            is_valid=False,
            message="Pro porotu je potřeba buď 'Celé jméno', nebo kombinace 'Jméno' + 'Příjmení'.",
            code="JURY_NAME_SHAPE_INVALID",
            field_key="fullname",
        )

