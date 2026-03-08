import datetime
from typing import Set, Any

from pandas import (DataFrame,
                    isna,
                    to_datetime,
                    to_timedelta)

from classes import Performance
from .table_parser import TableParser


class PerformanceParser(TableParser):
    def parse(self, df: DataFrame) -> Set[Any]:
        result = set()
        for idx, row in df.iterrows():  # idx is the pandas row index (preserved from original df)
            # Attempt to parse competition_id, skip row if it's missing or invalid
            try:
                if isna(row[self._cols["competition_id"]]):
                    continue
                competition_id = int(row[self._cols["competition_id"]])
            except ValueError:
                continue
            try:
                start_time = to_datetime(
                    row[self._cols["start_time"]],
                    format="%H:%M:%S"
                ).to_pydatetime()

                duration = int(to_timedelta(row[self._cols["duration"]]).total_seconds() // 60)
                round_type = row[self._cols["round_type"]]

                try:
                    end_time = to_datetime(
                        row[self._cols["end_time"]],
                        format="%H:%M:%S"
                    ).to_pydatetime()
                except KeyError:
                    end_time = start_time + datetime.timedelta(minutes=duration)
            except Exception as e:
                print(f"Problem while parsing competition in row {idx} - {row}: {e}")
                continue

            result.add(Performance(
                start_time=start_time,
                duration=duration,
                source_row=idx,
                competition_id=competition_id,
                round_type=round_type,
                end_time=end_time))

        return result
