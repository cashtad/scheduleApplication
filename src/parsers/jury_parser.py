from pandas import DataFrame, isna

from classes import Jury
from core import TABLE_CONFIGS
from .table_parser import TableParser


class JuryParser(TableParser):
    """Parses a jury DataFrame into a set of Jury objects."""

    _CONFIG = TABLE_CONFIGS["jury"]

    def parse(self, df: DataFrame) -> set[Jury]:
        result = set()
        prefix = self._cols["assignment_prefix"]
        competition_cols = self.get_filtered_competition_cols(df)

        for idx, row in df.iterrows():
            if isna(row[self._cols["id"]]) or row[self._cols["id"]] == "":
                continue
            try:
                name    = str(row[self._cols["name"]]).strip()
                surname = str(row[self._cols["surname"]]).strip()
                assignments = frozenset(
                    int(str(col).removeprefix(prefix))
                    for col in competition_cols
                    if str(row[col]).strip() == "1"
                )
            except Exception as exc:
                print(f"Skipping jury row #{idx}: {exc}")
                continue

            result.add(Jury(
                name=name,
                surname=surname,
                fullname=f"{name} {surname}",
                competition_ids=assignments,
            ))
        return result