from abc import ABC, abstractmethod

from pandas import DataFrame


class TableParser(ABC):
    """Abstract base for all table parsers."""

    def __init__(self, columns: dict[str, str]):
        self._cols = columns

    @abstractmethod
    def parse(self, df: DataFrame):
        pass

    def get_filtered_competition_cols(self, df: DataFrame) -> set:
        """Return column names that represent competition assignments.

        If `assignment_prefix` is empty, returns columns whose names are
        pure integers (e.g. "1", "2", "42").
        Otherwise returns columns that start with the given prefix.
        """
        prefix = self._cols["assignment_prefix"]
        if prefix == "":
            return {col for col in df.columns if self._is_pure_int(str(col).strip())}
        return {col for col in df.columns if str(col).startswith(prefix)}

    @staticmethod
    def _is_pure_int(value: str) -> bool:
        """Return True if *value* represents a non-negative integer."""
        return value.isdigit()