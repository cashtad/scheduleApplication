import datetime

import pandas as pd
from typing import List, Dict, Any

from src.classes.performance import Performance


class PerformanceParser:
    def __init__(self, columns: Dict[str, str]):
        self._cols = columns

    def parse(self, df: pd.DataFrame) -> List[Any]:
        result = []
        for _, row in df.iterrows():
            try:
                competition_id = int(row[self._cols["competition_id"]])
            except ValueError:
                continue

            start_time = pd.to_datetime(
                row[self._cols["start_time"]],
                format="%H:%M:%S"
            ).to_pydatetime()
            duration = int(pd.to_timedelta(row[self._cols["duration"]]).total_seconds() // 60)
            round_type = row[self._cols["round_type"]]

            try:
                end_time = pd.to_datetime(
                    row[self._cols["end_time"]],
                    format="%H:%M:%S"
                ).to_pydatetime()
            except KeyError:
                end_time = start_time + datetime.timedelta(minutes=duration)

            result.append(
                (Performance(
                    start_time=start_time,
                    end_time=end_time,
                    duration=duration,
                    round_type=round_type,
                    competition=None
                ), competition_id))
        return result