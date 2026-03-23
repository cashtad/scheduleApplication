from pandas import DataFrame, isna

from classes import Competitor
from core import TABLE_CONFIGS, EntityParseStats
from .table_parser import TableParser


class CompetitorsParser(TableParser):
    _CONFIG = TABLE_CONFIGS["competitors"]

    def parse(self, df: DataFrame) -> tuple[set[Competitor], EntityParseStats]:
        self.validate_mapping_columns(df, [f.key for f in self._CONFIG.fields if not f.virtual_key], virtual_keys=set(f.key for f in self._CONFIG.fields if f.virtual_key))
        result = set()
        stats = EntityParseStats()

        prefix = self._cols["assignment_prefix"]
        competition_cols = self.get_filtered_competition_cols(df)

        for idx, row in df.iterrows():
            count_raw = row[self._cols["count"]]
            if isna(count_raw) or str(count_raw).strip() not in {"1", "2"}:
                stats.add_skip(f"competitor row #{idx}: invalid count")
                continue

            try:
                count = int(str(count_raw).strip())
                full_name_1 = str(row[self._cols["p1_name_surname"]]).strip()
                full_name_2 = str(row[self._cols["p2_name_surname"]]).strip() if count == 2 else None

                assignments = frozenset(
                    int(str(col).removeprefix(prefix))
                    for col in competition_cols
                    if str(row[col]).strip() == "1"
                )

                result.add(Competitor(
                    count=count,
                    full_name_1=full_name_1,
                    full_name_2=full_name_2,
                    competition_ids=assignments,
                ))
                stats.parsed += 1
            except Exception as exc:
                stats.add_skip(f"competitor row #{idx}: {exc}")

        return result, stats