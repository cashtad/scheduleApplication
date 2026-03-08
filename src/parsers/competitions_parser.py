from typing import Set

from pandas import DataFrame

from classes import Competition
from .table_parser import TableParser


class CompetitionParser(TableParser):

    def parse(self, df: DataFrame) -> Set[Competition]:
        result = set()
        for idx, row in df.iterrows():
            try:
                id = int(row[self._cols["id"]])
                name = row[self._cols["title"]]
                discipline = row[self._cols["discipline"]]
                age = row[self._cols["age"]]
                rank = row[self._cols["rank"]]
                competitor_count = int(row[self._cols["competitor_count"]])
                round_count = int(row[self._cols["round_count"]])
            except Exception as e:
                print(f"Problem while parsing competition in row #{idx} - {row}: {e}")
                continue

            result.add(Competition(
                id=id,
                name=name,
                discipline=discipline,
                age=age,
                rank=rank,
                competitor_count=competitor_count,
                round_count=round_count,
            ))
        return result
