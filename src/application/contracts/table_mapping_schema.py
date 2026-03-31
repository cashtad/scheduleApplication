from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MappingField:
    key: str
    label: str
    required: bool = True
    virtual: bool = False


@dataclass(frozen=True, slots=True)
class TableMappingSchema:
    table_key: str
    fields: tuple[MappingField, ...]

    def field_keys(self) -> list[str]:
        return [f.key for f in self.fields]

    def required_keys(self) -> list[str]:
        return [f.key for f in self.fields if f.required]

    def virtual_keys(self) -> set[str]:
        return {f.key for f in self.fields if f.virtual}


TABLE_MAPPING_SCHEMAS: dict[str, TableMappingSchema] = {
    "competitions": TableMappingSchema(
        table_key="competitions",
        fields=(
            MappingField("id", "ID soutěže", True),
            MappingField("name", "Název", True),
            MappingField("discipline", "Disciplína", True),
            MappingField("amount_of_rounds", "Počet kol", True),
        ),
    ),
    "competitors": TableMappingSchema(
        table_key="competitors",
        fields=(
            MappingField("count", "Počet závodníků páru", True),
            MappingField("p1_name_surname", "Jméno závodníka 1", True),
            MappingField("p2_name_surname", "Jméno závodníka 2", False),
            MappingField("assignment_prefix", "Prefix pro ID soutěží (např. '#')", True, virtual=True),
        ),
    ),
    "jury": TableMappingSchema(
        table_key="jury",
        fields=(
            MappingField("fullname", "Celé jméno", False),
            MappingField("name", "Jméno", False),
            MappingField("surname", "Příjmení", False),
            MappingField("assignment_prefix", "Prefix pro ID soutěží (např. '#')", True, virtual=True),
        ),
    ),
    "schedule": TableMappingSchema(
        table_key="schedule",
        fields=(
            MappingField("competition_id", "ID soutěže", True),
            MappingField("start_time", "Začátek", True),
            MappingField("duration", "Délka (min)", True),
            MappingField("round_type", "Typ kola", True),
        ),
    ),
}