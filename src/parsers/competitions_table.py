import pandas as pd
from typing import List, Dict

from src.classes.competition import Competition


class CompetitionParser:
    def __init__(self, columns: Dict[str, str]):
        self._cols = columns

    def parse(self, df: pd.DataFrame) -> List[Competition]:
        result = []
        for _, row in df.iterrows():
            result.append(
                Competition(
                    id=int(row[self._cols["id"]]),
                    name=row[self._cols["title"]],
                    discipline=row[self._cols["discipline"]],
                    age=row[self._cols["age"]],
                    rank=row[self._cols["rank"]],
                    competitor_count=row[self._cols["competitor_count"]],
                    round_count=int(row[self._cols["round_count"]] or 0),
                    competitors=[],
                    performances=[],
                    juries=[],
                )
            )
        return result
