from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional
import datetime
from pandas import to_datetime, to_timedelta, isna


@dataclass(frozen=True)
class FieldDef:
    key:           str
    label:         str
    required:      bool
    attr:          Optional[str]              = None
    parse:         Optional[Callable[[Any], Any]] = None
    skip_if_empty: bool                       = False

    @property
    def attr_name(self) -> str:
        return self.attr if self.attr is not None else self.key


@dataclass(frozen=True)
class TableConfig:
    key:          str                    # e.g. "competitions"
    display_name: str                    # e.g. "Tabulka soutěží"
    fields:       tuple[FieldDef, ...]   #

def _parse_int(v: Any) -> int:
    return int(v)

def _parse_time(v: Any) -> datetime.datetime:
    return to_datetime(str(v), format="%H:%M:%S").to_pydatetime()

def _parse_duration_minutes(v: Any) -> int:
    return int(to_timedelta(str(v)).total_seconds() // 60)

def _parse_str(v: Any) -> str:
    return str(v).strip()


TABLE_CONFIGS: dict[str, TableConfig] = {
    "competitions": TableConfig(
        key="competitions",
        display_name="Tabulka soutěží",
        fields=(
            FieldDef("id",               "ID soutěže",       required=True,  attr="id",               parse=_parse_int,  skip_if_empty=True),
            FieldDef("title",            "Název",            required=True,  attr="name",              parse=_parse_str),
            FieldDef("discipline",       "Disciplína",       required=True,  parse=_parse_str),
            FieldDef("age",              "Věková kategorie", required=True,  parse=_parse_str),
            FieldDef("rank",             "Třída",            required=True,  parse=_parse_str),
            FieldDef("competitor_count", "Počet závodníků",  required=True,  parse=_parse_int),
            FieldDef("round_count",      "Počet kol",        required=True,  parse=_parse_int),
        ),
    ),
    "competitors": TableConfig(
        key="competitors",
        display_name="Tabulka závodníků",
        fields=(
            FieldDef("count",             "Počet závodníků páru", required=True,  parse=_parse_int,  skip_if_empty=True),
            FieldDef("p1_name_surname",   "Jméno závodníka 1",    required=True,  attr="full_name_1", parse=_parse_str),
            FieldDef("p2_name_surname",   "Jméno závodníka 2",    required=False, attr="full_name_2", parse=_parse_str),
            FieldDef("assignment_prefix", "Prefix přiřazení",     required=True),  # handled separately
        ),
    ),
    "jury": TableConfig(
        key="jury",
        display_name="Tabulka porotců",
        fields=(
            FieldDef("id",                "ID porotce",    required=True,  skip_if_empty=True),
            FieldDef("name",              "Jméno",         required=True,  parse=_parse_str),
            FieldDef("surname",           "Příjmení",      required=True,  parse=_parse_str),
            FieldDef("assignment_prefix", "Prefix přiřazení", required=True),
        ),
    ),
    "schedule": TableConfig(
        key="schedule",
        display_name="Tabulka harmonogramu",
        fields=(
            FieldDef("competition_id", "ID soutěže",     required=True,  parse=_parse_int,              skip_if_empty=True),
            FieldDef("start_time",     "Čas začátku",    required=True,  parse=_parse_time),
            FieldDef("duration",       "Délka (minuty)", required=True,  parse=_parse_duration_minutes),
            FieldDef("round_type",     "Typ kola",       required=True,  parse=_parse_str),
        ),
    ),
}