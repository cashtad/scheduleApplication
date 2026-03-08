from typing import Set

from pandas import DataFrame, isna

from classes import Jury
from .table_parser import TableParser


class JuryParser(TableParser):
    def parse(self, df: DataFrame) -> Set[Jury]:
        result = set()

        prefix = self._cols["assignment_prefix"]
        filtered_competition_cols = self.get_filtered_competition_cols(df)
        for idx, row in df.iterrows():
            if isna(row[self._cols["id"]]) or row[self._cols["id"]] == "":
                continue  # skip useless rows

            try:
                name = str(row[self._cols["name"]]).strip()
                surname = str(row[self._cols["surname"]]).strip()
                fullname = name + " " + surname

                assignments = frozenset(
                    int(str(col).removeprefix(prefix))
                    for col in filtered_competition_cols
                    if str(row[col]).strip() == "1")
            except Exception as e:
                print(f"Problem while parsing competition in row #{idx} - {row}: {e}")
                continue

            result.add(Jury(
                name=name,
                surname=surname,
                fullname=fullname,
                competition_ids=assignments),
            )

        return result
