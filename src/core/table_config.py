from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldDef:
    """Definition of one logical field for column mapping."""

    key: str       # logical name used in column_mapping dict
    label: str     # human-readable label shown in UI
    required: bool  # whether it's mandatory


@dataclass(frozen=True)
class TableConfig:
    """Complete configuration for one table type."""

    key: str                      # e.g. "competitions"
    display_name: str             # e.g. "Tabulka soutěží"
    fields: tuple[FieldDef, ...]  # ordered field definitions


TABLE_CONFIGS: dict[str, TableConfig] = {
    "competitions": TableConfig(
        key="competitions",
        display_name="Tabulka soutěží",
        fields=(
            FieldDef("id",               "ID soutěže",           required=True),
            FieldDef("title",            "Název",                required=True),
            FieldDef("discipline",       "Disciplína",           required=True),
            FieldDef("age",              "Věková kategorie",     required=True),
            FieldDef("rank",             "Třída",                required=True),
            FieldDef("competitor_count", "Počet závodníků",      required=True),
            FieldDef("round_count",      "Počet kol",            required=True),
        ),
    ),
    "competitors": TableConfig(
        key="competitors",
        display_name="Tabulka závodníků",
        fields=(
            FieldDef("count",             "Počet závodníků páru", required=True),
            FieldDef("p1_name_surname",   "Jméno závodníka 1",    required=True),
            FieldDef("p2_name_surname",   "Jméno závodníka 2",    required=False),
            FieldDef("assignment_prefix", "Prefix přiřazení",     required=True),
        ),
    ),
    "jury": TableConfig(
        key="jury",
        display_name="Tabulka porotců",
        fields=(
            FieldDef("id",                "ID porotce",           required=True),
            FieldDef("name",              "Jméno",                required=True),
            FieldDef("surname",           "Příjmení",             required=True),
            FieldDef("assignment_prefix", "Prefix přiřazení",     required=True),
        ),
    ),
    "schedule": TableConfig(
        key="schedule",
        display_name="Tabulka harmonogramu",
        fields=(
            FieldDef("competition_id", "ID soutěže",     required=True),
            FieldDef("start_time",     "Čas začátku",    required=True),
            FieldDef("duration",       "Délka (minuty)", required=True),
            FieldDef("round_type",     "Typ kola",       required=True),
            FieldDef("end_time",       "Čas konce",      required=False),
        ),
    ),
}
