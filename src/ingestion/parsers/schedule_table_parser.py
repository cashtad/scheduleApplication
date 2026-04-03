from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from pandas import DataFrame, to_datetime, to_timedelta

from src.domain import Performance
from src.ingestion.contracts import IngestionIssue, TableParseResult
from .base_table_parser import BaseTableParser


class ScheduleTableParser(BaseTableParser[Performance]):
    def __init__(self, mapping: dict[str, str]) -> None:
        super().__init__(table_key="schedule", mapping=mapping)

    def required_mapping_keys(self) -> list[str]:
        return ["competition_id", "start_time", "duration", "round_type"]

    def parse(self, df: DataFrame) -> TableParseResult[Performance]:
        self.validate_mapping_columns(df)

        issues: list[IngestionIssue] = []
        items: list[Performance] = []
        total_rows = len(df.index)
        parsed_rows = 0

        for row_index, row in df.iterrows():
            try:
                performance = self._parse_row(row_index=int(row_index), row=row)
                if performance is None:
                    issues.append(
                        self.make_row_warning(
                            row_index=int(row_index),
                            code="SCHEDULE_ROW_EMPTY_COMPETITION_ID",
                            message="Row skipped because competition_id is empty",
                            column_key="competition_id",
                        )
                    )
                    continue

                items.append(performance)
                parsed_rows += 1

            except Exception as exc:
                issues.append(
                    self.make_row_error(
                        row_index=int(row_index),
                        code="SCHEDULE_ROW_PARSE_FAILED",
                        message=f"Failed to parse schedule row: {exc}",
                    )
                )

        return self.build_result(
            items=items,
            issues=issues,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
        )

    def _parse_row(self, row_index: int, row: Any) -> Performance | None:
        competition_raw = row[self.mapping["competition_id"]]
        if self.is_empty(competition_raw):
            return None

        competition_id = self.as_int(competition_raw)
        start_time = self._parse_datetime(row[self.mapping["start_time"]])
        duration_minutes = self._parse_duration_minutes(row[self.mapping["duration"]])
        round_type = self.as_str(row[self.mapping["round_type"]])

        end_time = start_time + timedelta(minutes=duration_minutes)

        return Performance(
            start_time=start_time,
            end_time=end_time,
            duration=duration_minutes,
            round_type=round_type,
            competition_id=competition_id,
            source_row=row_index,
        )

    @staticmethod
    def _parse_datetime(raw: Any) -> datetime:
        if isinstance(raw, datetime):
            return raw
        text = str(raw).strip()
        if not text:
            raise ValueError("start_time is empty")

        # strict formats first
        for fmt in ("%H:%M", "%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                pass

        # pandas fallback
        return to_datetime(text, errors="raise").to_pydatetime()

    @staticmethod
    def _parse_duration_minutes(raw: Any) -> int:
        text = str(raw).strip()
        if not text:
            raise ValueError("duration is empty")
        if text.isdigit():
            value = int(text)
            if value <= 0:
                raise ValueError("duration must be > 0")
            return value

        td = to_timedelta(text, errors="raise")
        minutes = int(td.total_seconds() // 60)
        if minutes <= 0:
            raise ValueError("duration must be > 0")
        return minutes
