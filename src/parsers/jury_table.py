import pandas as pd
from typing import List, Dict, Any

from src.classes.competition import Competition
from src.classes.jury import Jury


class JuryParser:
    def __init__(self, columns: Dict[str, str]):
        self._cols = columns

    def parse(self, df: pd.DataFrame) -> List[Any]:
        prefix = self._cols["assignment_prefix"]
        competition_cols = [c for c in df.columns if c.startswith(prefix)]
        result = []
        for _, row in df.iterrows():
            if row[self._cols["id"]] == "":
                continue # skip useless rows
            assignments = [
                int(col.removeprefix(prefix))
                for col in competition_cols
                if str(row[col]).strip() == "1"

            ]
            jury = Jury(
                id=row[self._cols["id"]],
                name=row[self._cols["name"]] + " " + row[self._cols["surname"]],
            )
            result.append((jury, assignments))
        return result