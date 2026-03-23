import datetime
from pandas import DataFrame

from classes import Performance
from core import TABLE_CONFIGS, EntityParseStats
from .table_parser import TableParser


class PerformanceParser(TableParser):
    _CONFIG = TABLE_CONFIGS["schedule"]

    def parse(self, df: DataFrame) -> tuple[set[Performance], EntityParseStats]:
        self.validate_mapping_columns(df, ["competition_id", "start_time", "duration", "round_type"])
        result = set()
        stats = EntityParseStats()

        for idx, row in df.iterrows():
            try:
                performance = self._parse_row(idx, row)
                if performance is None:
                    stats.add_skip(f"schedule row #{idx}: empty competition_id")
                    continue
                result.add(performance)
                stats.parsed += 1
            except Exception as exc:
                stats.add_skip(f"schedule row #{idx}: {exc}")

        return result, stats

    def _parse_row(self, idx, row) -> Performance | None:
        competition_id_raw = row[self._cols["competition_id"]]
        if self._is_empty(competition_id_raw):
            return None

        competition_id = self._CONFIG.fields[0].parse(row[self._cols["competition_id"]])
        start_time = self._CONFIG.fields[1].parse(row[self._cols["start_time"]])
        duration = self._CONFIG.fields[2].parse(row[self._cols["duration"]])
        round_type = self._CONFIG.fields[3].parse(row[self._cols["round_type"]])
        end_time = start_time + datetime.timedelta(minutes=duration)

        return Performance(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            round_type=round_type,
            competition_id=competition_id,
            source_row=idx,
        )