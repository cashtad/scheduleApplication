import pandas as pd
from typing import List, Dict, Any

from src.classes.performance import Performance


class PerformanceParser:
    def __init__(self, columns: Dict[str, str]):
        self._cols = columns

    def parse(self, df: pd.DataFrame) -> List[Any]:
        result = []
        for _, row in df.iterrows():
            if row[self._cols["competitor_number"]] == "":
                continue # skip useless rows

            result.append(
                (Performance(
                    start_time=row[self._cols["start_time"]],
                    end_time=row[self._cols["end_time"]],
                    duration=row[self._cols["duration"]],
                    round_type=row[self._cols["round_type"]],
                    competition=None
                ), int(row[self._cols["competitor_number"]])))
        return result