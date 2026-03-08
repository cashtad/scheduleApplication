import pandas as pd
from typing import List, Dict, Any

from src.classes.competitor import Competitor


class CompetitorsParser:
    def __init__(self, columns: Dict[str, str]):
        self._cols = columns

    def parse(self, df: pd.DataFrame) -> List[Any]:
        prefix = self._cols["assignment_prefix"]
        competition_cols = [c for c in df.columns if str(c).startswith(prefix)]

        filtered_competition_cols = set()

        for col in competition_cols:
            temp = str(col).strip().removeprefix(prefix)
            for i, char in enumerate(temp):
                if not char.isdigit():
                    break
                elif i == len(temp) - 1:
                    filtered_competition_cols.add(col)

        result = []
        for i, row in df.iterrows():
            count = row[self._cols["count"]]
            full_name_1 = str(row[self._cols["p1_name_surname"]].strip())
            full_name_2 = str(row[self._cols["p2_name_surname"]].strip())  if count == "2" else None

            assignments = [
                int(str(col).removeprefix(prefix))
                for col in filtered_competition_cols
                if str(row[col]).strip() == "1"

            ]
            try:
                competitor = Competitor(
                    id=str(i),
                    count=int(count),
                    full_name_1=full_name_1,
                    full_name_2=full_name_2,
                )
            except ValueError:
                print(f"Invalid competitor count '{count}' for row {i}, skipping")
                continue # skip rows with invalid count
            result.append((competitor, assignments))
        return result