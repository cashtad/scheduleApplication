from __future__ import annotations

from pandas import DataFrame, read_excel, ExcelFile

from src.application.ports import ExcelReaderPort


class PandasExcelReader(ExcelReaderPort):
    def read(self, file_path: str, sheet_name: str | None) -> DataFrame:
        with ExcelFile(file_path) as xls:
            df = read_excel(xls, sheet_name=sheet_name, dtype=str)
        return df.fillna("")

    def get_sheet_names(self, file_path: str) -> list[str | int]:
        with ExcelFile(file_path) as xls:
            names = list(xls.sheet_names)
        return names
