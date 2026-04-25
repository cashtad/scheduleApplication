from __future__ import annotations

"""Unified registry for the four fixed tables used by the application."""

from dataclasses import dataclass
from enum import Enum


class TableKey(str, Enum):
    COMPETITIONS = "competitions"
    COMPETITORS = "competitors"
    JURY = "jury"
    SCHEDULE = "schedule"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class MappingField:
    key: str
    label: str
    required: bool = True
    virtual: bool = False


@dataclass(frozen=True, slots=True)
class TableMappingSchema:
    table_key: TableKey
    fields: tuple[MappingField, ...]

    def field_keys(self) -> list[str]:
        return [field.key for field in self.fields]

    def required_keys(self) -> list[str]:
        return [field.key for field in self.fields if field.required]

    def virtual_keys(self) -> set[str]:
        return {field.key for field in self.fields if field.virtual}

    @property
    def table_key_value(self) -> str:
        return self.table_key.value


@dataclass(frozen=True, slots=True)
class TableSpec:
    key: TableKey
    label_cz: str
    mapping_schema: TableMappingSchema
    uses_assignment_columns: bool = False

    @property
    def table_key(self) -> str:
        return self.key.value


def _build_schema(table_key: TableKey, fields: tuple[MappingField, ...]) -> TableMappingSchema:
    return TableMappingSchema(table_key=table_key, fields=fields)


TABLE_REGISTRY: dict[TableKey, TableSpec] = {
    TableKey.COMPETITIONS: TableSpec(
        key=TableKey.COMPETITIONS,
        label_cz="Soutěže",
        mapping_schema=_build_schema(
            TableKey.COMPETITIONS,
            (
                MappingField("id", "ID soutěže", True),
                MappingField("name", "Název", True),
                MappingField("discipline", "Disciplína", True),
                MappingField("amount_of_rounds", "Počet kol", False),
            ),
        ),
    ),
    TableKey.COMPETITORS: TableSpec(
        key=TableKey.COMPETITORS,
        label_cz="Soutěžící",
        mapping_schema=_build_schema(
            TableKey.COMPETITORS,
            (
                MappingField("p1_name_surname", "Jméno soutěžícího 1", True),
                MappingField("p2_name_surname", "Jméno soutěžícího 2", False),
                MappingField("assignment_prefix", "Prefix pro ID soutěží (např. '#')", False, virtual=True),
            ),
        ),
        uses_assignment_columns=True,
    ),
    TableKey.JURY: TableSpec(
        key=TableKey.JURY,
        label_cz="Porota",
        mapping_schema=_build_schema(
            TableKey.JURY,
            (
                MappingField("fullname", "Celé jméno", False),
                MappingField("name", "Jméno", False),
                MappingField("surname", "Příjmení", False),
                MappingField("assignment_prefix", "Prefix pro ID soutěží (např. '#')", False, virtual=True),
            ),
        ),
        uses_assignment_columns=True,
    ),
    TableKey.SCHEDULE: TableSpec(
        key=TableKey.SCHEDULE,
        label_cz="Harmonogram",
        mapping_schema=_build_schema(
            TableKey.SCHEDULE,
            (
                MappingField("competition_id", "ID soutěže", True),
                MappingField("start_time", "Začátek", True),
                MappingField("duration", "Délka (min)", True),
                MappingField("round_type", "Typ kola", True),
            ),
        ),
    ),
}


def _normalize_table_key(table_key: str | TableKey) -> TableKey:
    return table_key if isinstance(table_key, TableKey) else TableKey(table_key)


def get_table_spec(table_key: TableKey) -> TableSpec:
    return TABLE_REGISTRY[_normalize_table_key(table_key)]


def required_table_keys() -> tuple[TableKey, ...]:
    return tuple(TABLE_REGISTRY.keys())

