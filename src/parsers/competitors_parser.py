from typing import Set

from pandas import DataFrame, isna

from classes import Competitor
from .table_parser import TableParser


class CompetitorsParser(TableParser):
    def parse(self, df: DataFrame) -> Set[Competitor]:
        filtered_competition_cols = self.get_filtered_competition_cols(df)

        result = set()
        for idx, row in df.iterrows():
            if isna(row[self._cols["count"]]) or str(row[self._cols["count"]]).strip() not in {"1", "2"}:
                continue  # skip useless rows
            try:
                count = int(row[self._cols["count"]])
                full_name_1 = str(row[self._cols["p1_name_surname"]].strip())
                full_name_2 = str(row[self._cols["p2_name_surname"]].strip()) if count == "2" else None

                assignments = set(
                    int(str(col).removeprefix(prefix))
                    for col in filtered_competition_cols
                    if str(row[col]).strip() == "1")
            except:
                print(f"Problem while parsing competitor in row #{idx} - {row}")
                continue

            result.add(Competitor(
                count=count,
                full_name_1=full_name_1,
                full_name_2=full_name_2,
                competition_ids=assignments))
        return result
