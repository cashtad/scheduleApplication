from __future__ import annotations

from typing import Any

from pandas import DataFrame

from src.domain import Competition
from ..contracts import IngestionIssue, TableParseResult
from .base_table_parser import BaseTableParser


class CompetitionTableParser(BaseTableParser[Competition]):
    def __init__(self, mapping: dict[str, str]) -> None:
        super().__init__(table_key="competitions", mapping=mapping)

    def required_mapping_keys(self) -> list[str]:
        return [
            "id",
            "name",
            "discipline",
            "amount_of_rounds",
        ]

    def parse(self, df: DataFrame) -> TableParseResult[Competition]:
        self.validate_mapping_columns(df)

        issues: list[IngestionIssue] = []
        items: list[Competition] = []
        total_rows = len(df.index)
        parsed_rows = 0

        for row_index, row in df.iterrows():
            try:
                competition = self._parse_row(row)
                items.append(competition)
                parsed_rows += 1
            except Exception as exc:
                issues.append(
                    self.make_row_error(
                        row_index=int(row_index),
                        code="COMPETITION_ROW_PARSE_FAILED",
                        message=f"Failed to parse competition row: {exc}",
                    )
                )

        return self.build_result(
            items=items,
            issues=issues,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
        )

    def _parse_row(self, row: Any) -> Competition:
        id_value = self.as_int(row[self.mapping["id"]])
        name = self.as_str(row[self.mapping["name"]])
        discipline = self.as_str(row[self.mapping["discipline"]])
        amount_of_rounds = self.as_int(row[self.mapping["amount_of_rounds"]])

        return Competition(
            id=id_value,
            name=name,
            discipline=discipline,
            amount_of_rounds=amount_of_rounds,
        )