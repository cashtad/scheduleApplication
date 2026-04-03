from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pandas import DataFrame

from ..contracts import (
    FullIngestionResult,
    IngestionIssue,
    IngestionSeverity,
    TableInput,
    TableParseResult,
)
from ..parsers import (
    CompetitionTableParser,
    CompetitorTableParser,
    CompetitorParserConfig,
    JuryParserConfig,
    JuryTableParser,
    ScheduleTableParser,
)
from .assignment_columns_selector import AssignmentColumnsMode
from src.domain import Competition, Competitor, JuryMember, Performance
from src.infrastructure import ExcelReader


@dataclass(frozen=True, slots=True)
class IngestionServiceConfig:
    competitors_assignment_mode: AssignmentColumnsMode = AssignmentColumnsMode.PREFIX
    jury_assignment_mode: AssignmentColumnsMode = AssignmentColumnsMode.PREFIX
    assigned_markers: frozenset[str] = frozenset({"1"})


class TableIngestionService:
    def __init__(
        self, excel_reader: ExcelReader, config: IngestionServiceConfig | None = None
    ) -> None:
        self._excel_reader = excel_reader
        self._config = config or IngestionServiceConfig()

    def ingest(self, inputs: Iterable[TableInput]) -> FullIngestionResult:
        by_key = {x.table_key: x for x in inputs}

        competitions_result, competitions_schema, _ = self._ingest_competitions(
            by_key.get("competitions")
        )
        competitors_result, competitors_schema, _ = self._ingest_competitors(
            by_key.get("competitors")
        )
        jury_result, jury_schema, _ = self._ingest_jury(by_key.get("jury"))
        schedule_result, schedule_schema, schedule_raw_df = self._ingest_schedule(
            by_key.get("schedule")
        )

        schema_issues = (
            competitions_schema + competitors_schema + jury_schema + schedule_schema
        )
        schema_issues = self._deduplicate_issues(schema_issues)

        raw_tables: dict[str, DataFrame] = {}
        if schedule_raw_df is not None:
            raw_tables["schedule"] = schedule_raw_df

        return FullIngestionResult(
            competitions=competitions_result,
            competitors=competitors_result,
            jury_members=jury_result,
            performances=schedule_result,
            schema_issues=schema_issues,
            raw_tables=raw_tables,
        )

    # --------------------------
    # Per-table ingestion
    # --------------------------

    def _ingest_competitions(
        self, table_input: TableInput | None
    ) -> tuple[TableParseResult[Competition], list[IngestionIssue], DataFrame | None]:
        if table_input is None:
            return (
                self._empty_parse_result("competitions"),
                [self._missing_table_issue("competitions")],
                None,
            )

        parser = CompetitionTableParser(mapping=table_input.mapping)
        return self._read_validate_parse(table_input, parser)

    def _ingest_competitors(
        self, table_input: TableInput | None
    ) -> tuple[TableParseResult[Competitor], list[IngestionIssue], DataFrame | None]:
        if table_input is None:
            return (
                self._empty_parse_result("competitors"),
                [self._missing_table_issue("competitors")],
                None,
            )

        parser = CompetitorTableParser(
            mapping=table_input.mapping,
            config=CompetitorParserConfig(
                assignment_mode=self._config.competitors_assignment_mode,
                assigned_markers=self._config.assigned_markers,
            ),
        )
        return self._read_validate_parse(table_input, parser)

    def _ingest_jury(
        self, table_input: TableInput | None
    ) -> tuple[TableParseResult[JuryMember], list[IngestionIssue], DataFrame | None]:
        if table_input is None:
            return (
                self._empty_parse_result("jury"),
                [self._missing_table_issue("jury")],
                None,
            )

        parser = JuryTableParser(
            mapping=table_input.mapping,
            config=JuryParserConfig(
                assignment_mode=self._config.jury_assignment_mode,
                assigned_markers=self._config.assigned_markers,
            ),
        )
        return self._read_validate_parse(table_input, parser)

    def _ingest_schedule(
        self, table_input: TableInput | None
    ) -> tuple[TableParseResult[Performance], list[IngestionIssue], DataFrame | None]:
        if table_input is None:
            return (
                self._empty_parse_result("schedule"),
                [self._missing_table_issue("schedule")],
                None,
            )

        parser = ScheduleTableParser(mapping=table_input.mapping)
        return self._read_validate_parse(table_input, parser)

    def _read_validate_parse(
        self, table_input: TableInput, parser
    ) -> tuple[TableParseResult, list[IngestionIssue], DataFrame | None]:
        table_key = table_input.table_key
        schema_issues: list[IngestionIssue] = []

        file_issue = TableIngestionService._validate_file_path(table_input)
        if file_issue is not None:
            return self._empty_parse_result(table_key), [file_issue], None

        sheet_issue = self._validate_sheet_exists(table_input)
        if sheet_issue is not None:
            return self._empty_parse_result(table_key), [sheet_issue], None

        try:
            df = self._excel_reader.read(table_input.file_path, table_input.sheet_name)
        except Exception as exc:
            return (
                self._empty_parse_result(table_key),
                [
                    IngestionIssue(
                        table_key=table_key,
                        code="EXCEL_READ_FAILED",
                        message=f"Failed to read excel table: {exc}",
                        severity=IngestionSeverity.ERROR,
                        context={
                            "file_path": table_input.file_path,
                            "sheet_name": table_input.sheet_name,
                        },
                    )
                ],
                None,
            )

        signature_issue = TableIngestionService._validate_signature(
            table_input, [str(c) for c in df.columns]
        )
        if signature_issue is not None:
            schema_issues.append(signature_issue)

        try:
            parse_result = parser.parse(df)
        except Exception as exc:
            parse_result = self._empty_parse_result(table_key)
            schema_issues.append(
                IngestionIssue(
                    table_key=table_key,
                    code="TABLE_PARSE_FAILED",
                    message=f"Parser failed before row parsing: {exc}",
                    severity=IngestionSeverity.ERROR,
                )
            )

        return parse_result, schema_issues, df

    # --------------------------
    # Schema checks
    # --------------------------
    @staticmethod
    def _validate_file_path(table_input: TableInput) -> IngestionIssue | None:
        if not table_input.file_path:
            return IngestionIssue(
                table_key=table_input.table_key,
                code="FILE_PATH_EMPTY",
                message="File path is empty",
                severity=IngestionSeverity.ERROR,
            )

        if not Path(table_input.file_path).exists():
            return IngestionIssue(
                table_key=table_input.table_key,
                code="FILE_NOT_FOUND",
                message="Configured file does not exist",
                severity=IngestionSeverity.ERROR,
                context={"file_path": table_input.file_path},
            )

        return None

    def _validate_sheet_exists(self, table_input: TableInput) -> IngestionIssue | None:
        try:
            sheet_names = self._excel_reader.get_sheet_names(table_input.file_path)
        except Exception as exc:
            return IngestionIssue(
                table_key=table_input.table_key,
                code="SHEET_ENUMERATION_FAILED",
                message=f"Failed to read sheet names: {exc}",
                severity=IngestionSeverity.ERROR,
                context={"file_path": table_input.file_path},
            )

        if table_input.sheet_name is None:
            return None

        if table_input.sheet_name not in sheet_names:
            return IngestionIssue(
                table_key=table_input.table_key,
                code="SHEET_NOT_FOUND",
                message=f"Sheet '{table_input.sheet_name}' not found",
                severity=IngestionSeverity.ERROR,
                context={
                    "file_path": table_input.file_path,
                    "sheet_name": table_input.sheet_name,
                    "available_sheets": sheet_names,
                },
            )
        return None

    @staticmethod
    def _validate_signature(
        table_input: TableInput, current_columns: list[str]
    ) -> IngestionIssue | None:
        # Signature mismatch is warning-level: user may intentionally reorder/rename columns and remap.
        if not table_input.column_signature:
            return None

        if list(table_input.column_signature) == list(current_columns):
            return None

        return IngestionIssue(
            table_key=table_input.table_key,
            code="COLUMN_SIGNATURE_MISMATCH",
            message="Current columns differ from saved mapping signature",
            severity=IngestionSeverity.WARNING,
            context={
                "saved_signature": list(table_input.column_signature),
                "current_columns": list(current_columns),
            },
        )

    # --------------------------
    # Helpers
    # --------------------------

    @staticmethod
    def _missing_table_issue(table_key: str) -> IngestionIssue:
        return IngestionIssue(
            table_key=table_key,
            code="TABLE_INPUT_MISSING",
            message="Table input is missing in session",
            severity=IngestionSeverity.ERROR,
        )

    @staticmethod
    def _empty_parse_result(table_key: str) -> TableParseResult:
        return TableParseResult(
            table_key=table_key,
            items=[],
            issues=[],
            total_rows=0,
            parsed_rows=0,
            skipped_rows=0,
        )

    @staticmethod
    def _deduplicate_issues(issues: list[IngestionIssue]) -> list[IngestionIssue]:
        unique: dict[tuple, IngestionIssue] = {}
        for issue in issues:
            key = issue.dedup_key()
            unique[key] = issue
        return list(unique.values())
