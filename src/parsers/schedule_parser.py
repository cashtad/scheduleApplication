import datetime
from pandas import DataFrame, isna, to_datetime, to_timedelta

from classes import Performance
from core import TABLE_CONFIGS
from .table_parser import TableParser


class PerformanceParser(TableParser):
    """Parses a schedule DataFrame into a set of Performance objects."""

    _CONFIG = TABLE_CONFIGS["schedule"]

    def parse(self, df: DataFrame) -> set[Performance]:
        result = set()
        for idx, row in df.iterrows():
            try:
                performance = self._parse_row(idx, row)
            except Exception as exc:
                print(f"Skipping schedule row #{idx}: {exc}")
                continue
            if performance is not None:
                result.add(performance)
        return result

    def _parse_row(self, idx, row) -> Performance | None:
        """Parse a single row. Returns None if competition_id is missing."""
        competition_id_raw = row[self._cols["competition_id"]]
        if self._is_empty(competition_id_raw):
            return None

        competition_id = int(competition_id_raw)
        start_time     = to_datetime(row[self._cols["start_time"]], format="%H:%M:%S").to_pydatetime()
        duration       = int(to_timedelta(row[self._cols["duration"]]).total_seconds() // 60)
        round_type     = str(row[self._cols["round_type"]])
        end_time       = start_time + datetime.timedelta(minutes=duration)

        return Performance(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            round_type=round_type,
            competition_id=competition_id,
            source_row=idx,
        )