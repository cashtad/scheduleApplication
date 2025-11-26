import pandas as pd
from typing import List, Dict, Any

from src.classes.competitor import Competitor


class CompetitorsParser:
    def __init__(self, columns: Dict[str, str]):
        self._cols = columns

    def parse(self, df: pd.DataFrame) -> List[Any]:
        prefix = self._cols["assignment_prefix"]
        competition_cols = [c for c in df.columns if c.startswith(prefix)]
        result = []
        for i, row in df.iterrows():
            count = row[self._cols["count"]]
            full_name_1 = row[self._cols["p1_name_surname"]].strip()
            full_name_2 = None
            if count == "2":
                full_name_2 = row[self._cols["p2_name_surname"]].strip()
            assignments = [
                int(col.removeprefix(prefix))
                for col in competition_cols
                if str(row[col]).strip() == "1"

            ]
            competitor = Competitor(
                id=str(i),
                count=int(count),
                full_name_1=full_name_1,
                full_name_2=full_name_2,
            )
            result.append((competitor, assignments))
        return result