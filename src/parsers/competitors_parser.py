from pandas import DataFrame, isna

from classes import Competitor
from core import TABLE_CONFIGS
from .table_parser import TableParser


class CompetitorsParser(TableParser):
    """Parses a competitors DataFrame into a set of Competitor objects."""

    _CONFIG = TABLE_CONFIGS["competitors"]

    def parse(self, df: DataFrame) -> set[Competitor]:
        result = set()
        prefix = self._cols["assignment_prefix"]
        competition_cols = self.get_filtered_competition_cols(df)

        for idx, row in df.iterrows():
            count_raw = row[self._cols["count"]]
            if isna(count_raw) or str(count_raw).strip() not in {"1", "2"}:
                continue
            try:
                count       = int(str(count_raw).strip())
                full_name_1 = str(row[self._cols["p1_name_surname"]]).strip()
                full_name_2 = (
                    str(row[self._cols["p2_name_surname"]]).strip()
                    if count == 2 else None
                )
                assignments = frozenset(
                    int(str(col).removeprefix(prefix))
                    for col in competition_cols
                    if str(row[col]).strip() == "1"
                )
            except Exception as exc:
                print(f"Skipping competitor row #{idx}: {exc}")
                continue

            result.add(Competitor(
                count=count,
                full_name_1=full_name_1,
                full_name_2=full_name_2,
                competition_ids=assignments,
            ))
        return result