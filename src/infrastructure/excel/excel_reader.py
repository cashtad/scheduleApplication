from __future__ import annotations

from typing import Protocol

from pandas import DataFrame


class ExcelReader(Protocol):
    def read(self, file_path: str, sheet_name: str | None) -> DataFrame:
        ...

    def get_sheet_names(self, file_path: str) -> list[str]:
        ...