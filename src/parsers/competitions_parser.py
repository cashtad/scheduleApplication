from pandas import DataFrame

from classes import Competition
from core import TABLE_CONFIGS, EntityParseStats
from .table_parser import TableParser


class CompetitionParser(TableParser):
    _CONFIG = TABLE_CONFIGS["competitions"]

    def parse(self, df: DataFrame) -> tuple[set[Competition], EntityParseStats]:
        self.validate_mapping_columns(df, [f.key for f in self._CONFIG.fields])
        result = set()
        stats = EntityParseStats()

        for idx, row in df.iterrows():
            try:
                kwargs = self._extract_row(row)
                result.add(Competition(**kwargs))
                stats.parsed += 1
            except Exception as exc:
                stats.add_skip(f"competition row #{idx}: {exc}")

        return result, stats

    def _extract_row(self, row) -> dict:
        kwargs = {}
        for field in self._CONFIG.fields:
            col = self._cols[field.key]
            raw = row[col]
            if field.skip_if_empty and self._is_empty(raw):
                raise ValueError(f"'{field.key}' je prázdné")
            value = field.parse(raw) if field.parse else str(raw)
            kwargs[field.attr_name] = value
        return kwargs