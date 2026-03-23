from pandas import DataFrame, isna

from classes import Jury
from core import TABLE_CONFIGS, EntityParseStats
from .table_parser import TableParser


class JuryParser(TableParser):
    _CONFIG = TABLE_CONFIGS["jury"]

    def parse(self, df: DataFrame) -> tuple[set[Jury], EntityParseStats]:
        self.validate_mapping_columns(df, [f.key for f in self._CONFIG.fields if not f.virtual_key], virtual_keys=set(f.key for f in self._CONFIG.fields if f.virtual_key))
        result = set()
        stats = EntityParseStats()

        prefix = self._cols["assignment_prefix"]
        competition_cols = self.get_filtered_competition_cols(df)

        for idx, row in df.iterrows():
            if isna(row[self._cols["id"]]) or str(row[self._cols["id"]]).strip() == "":
                stats.add_skip(f"jury row #{idx}: empty id")
                continue
            try:
                name = str(row[self._cols["name"]]).strip()
                surname = str(row[self._cols["surname"]]).strip()
                assignments = frozenset(
                    int(str(col).removeprefix(prefix))
                    for col in competition_cols
                    if str(row[col]).strip() == "1"
                )
                result.add(Jury(
                    name=name,
                    surname=surname,
                    fullname=f"{name} {surname}",
                    competition_ids=assignments,
                ))
                stats.parsed += 1
            except Exception as exc:
                stats.add_skip(f"jury row #{idx}: {exc}")

        return result, stats