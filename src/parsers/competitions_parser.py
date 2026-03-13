from pandas import DataFrame

from classes import Competition
from core import TABLE_CONFIGS
from .table_parser import TableParser


class CompetitionParser(TableParser):
    """Parses a competitions DataFrame into a set of Competition objects.

    All field keys and type conversions are driven by TABLE_CONFIGS["competitions"],
    so adding/renaming a field only requires a change in table_config.py.
    """

    _CONFIG = TABLE_CONFIGS["competitions"]

    def parse(self, df: DataFrame) -> set[Competition]:
        result = set()
        for idx, row in df.iterrows():
            try:
                kwargs = self._extract_row(row)
            except Exception as exc:
                print(f"Skipping competition row #{idx}: {exc}")
                continue
            result.add(Competition(**kwargs))
        return result

    def _extract_row(self, row) -> dict:
        """Extract and type-convert all fields from *row* using the config."""
        kwargs = {}
        for field in self._CONFIG.fields:
            col = self._cols[field.key]
            raw = row[col]

            if field.skip_if_empty and self._is_empty(raw):
                raise ValueError(f"Required-skip field '{field.key}' is empty")

            value = field.parse(raw) if field.parse else str(raw)
            kwargs[field.attr_name] = value
        return kwargs