from __future__ import annotations

from pandas import DataFrame, read_excel, ExcelFile

from .excel_reader import ExcelReader


class PandasExcelReader(ExcelReader):
    def read(self, file_path: str, sheet_name: str | None) -> DataFrame:
        df = read_excel(file_path, sheet_name=sheet_name, dtype=str)
        return df.fillna("")

    def get_sheet_names(self, file_path: str) -> list[str]:
        xls = ExcelFile(file_path)
        return list(xls.sheet_names)