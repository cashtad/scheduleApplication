from abc import ABC, abstractmethod
from typing import Any

from pandas import DataFrame, isna

from core import MappingValidationError


class TableParser(ABC):
    """Abstract base for all table parsers."""

    def __init__(self, columns: dict[str, str]):
        self._cols = columns

    @abstractmethod
    def parse(self, df: DataFrame):
        pass

    def validate_mapping_columns(
        self,
        df: DataFrame,
        required_keys: list[str],
        virtual_keys: set[str] | None = None,
    ) -> None:
        virtual_keys = virtual_keys or set()

        missing_keys = [k for k in required_keys if k not in self._cols]
        if missing_keys:
            raise MappingValidationError(
                code="MAP_MISSING_KEYS",
                user_message=f"Chybí mapování pro pole: {', '.join(missing_keys)}",
                technical_message=f"Missing mapping keys: {missing_keys}",
            )

        keys_requiring_real_columns = [k for k in required_keys if k not in virtual_keys]
        missing_columns = [
            self._cols[k]
            for k in keys_requiring_real_columns
            if self._cols[k] not in df.columns
        ]
        if missing_columns:
            raise MappingValidationError(
                code="MAP_MISSING_COLUMNS",
                user_message=f"V tabulce chybí vybrané sloupce: {', '.join(missing_columns)}",
                technical_message=f"Missing columns in df: {missing_columns}",
            )

    def get_filtered_competition_cols(self, df: DataFrame) -> set:
        prefix = self._cols.get("assignment_prefix", "")
        if prefix == "":
            cols = {col for col in df.columns if self._is_pure_int(str(col).strip())}
        else:
            cols = {col for col in df.columns if str(col).startswith(prefix)}

        if not cols:
            raise MappingValidationError(
                code="MAP_ASSIGNMENT_PREFIX_EMPTY",
                user_message="Pro zadaný prefix přiřazení nebyl nalezen žádný sloupec.",
                technical_message=f"assignment_prefix='{prefix}' did not match any column",
            )
        return cols

    @staticmethod
    def _is_pure_int(value: str) -> bool:
        return value.isdigit()

    @staticmethod
    def _is_empty(v: Any) -> bool:
        try:
            return isna(v) or str(v).strip() == ""
        except Exception:
            return False