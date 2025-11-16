import pandas as pd
from pathlib import Path
from typing import Optional

class ExcelTableLoader:
    def __init__(self, path: str, sheet: Optional[str] = None):
        self._path = Path(path)
        self._sheet = sheet

    def load(self) -> pd.DataFrame:
        df = pd.read_excel(self._path, sheet_name=self._sheet, dtype=str)
        return df.fillna("")
