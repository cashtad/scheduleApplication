from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

from pandas import DataFrame, isna

from src.ingestion.contracts import IngestionIssue, IngestionSeverity, TableParseResult
from .errors import MappingValidationError, UserFacingParseError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ParseContext:
    table_key: str
    mapping: dict[str, str]


class BaseTableParser(ABC, Generic[T]):
    def __init__(self, table_key: str, mapping: dict[str, str]) -> None:
        self._ctx = ParseContext(table_key=table_key, mapping=dict(mapping))

    @property
    def table_key(self) -> str:
        return self._ctx.table_key

    @property
    def mapping(self) -> dict[str, str]:
        return self._ctx.mapping

    @abstractmethod
    def required_mapping_keys(self) -> list[str]: ...

    def virtual_mapping_keys(self) -> set[str]:
        return set()

    @abstractmethod
    def parse(self, df: DataFrame) -> TableParseResult[T]: ...

    # --------------------------
    # Mapping / schema validation
    # --------------------------

    def validate_mapping_columns(self, df: DataFrame) -> None:
        required_keys = self.required_mapping_keys()
        virtual_keys = self.virtual_mapping_keys()

        missing_keys = [k for k in required_keys if k not in self.mapping]
        if missing_keys:
            raise MappingValidationError(
                code="MAP_MISSING_KEYS",
                message=f"Chybějící klíče mapování: {', '.join(missing_keys)}",
                context={"missing_keys": missing_keys, "table_key": self.table_key},
            )

        keys_requiring_real_columns = [
            k for k in required_keys if k not in virtual_keys
        ]
        missing_columns = [
            self.mapping[k]
            for k in keys_requiring_real_columns
            if self.mapping[k] not in set(df.columns)
        ]
        if missing_columns:
            raise MappingValidationError(
                code="MAP_MISSING_COLUMNS",
                message=f"Namapované sloupce nebyly v tabulce nalezeny: {', '.join(missing_columns)}",
                context={
                    "missing_columns": missing_columns,
                    "table_key": self.table_key,
                },
            )

    # --------------------------
    # Row helpers
    # --------------------------

    @staticmethod
    def is_empty(value: Any) -> bool:
        try:
            na_value = isna(value)
            if isinstance(na_value, bool):
                return na_value or str(value).strip() == ""
            return str(value).strip() == ""
        except Exception:
            return False

    @staticmethod
    def as_str(value: Any) -> str:
        return str(value).strip()

    @staticmethod
    def as_int(value: Any, column_key: str | None = None) -> int:
        text = str(value).strip()
        try:
            return int(text)
        except (TypeError, ValueError):
            column_label = (
                f"Pole '{column_key}' musí obsahovat celé číslo"
                if column_key
                else "Hodnota musí být celé číslo"
            )
            raise UserFacingParseError(
                code="INVALID_INTEGER",
                message=column_label,
                column_key=column_key,
                context={"value": text},
            ) from None

    @staticmethod
    def row_to_dict(row: Any) -> dict[str, Any]:
        # pandas Series -> dict
        return cast(dict[str, Any], dict(row.items()))

    @staticmethod
    def as_row_index(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return -1

    def make_issue(
        self,
        code: str,
        message: str,
        severity: IngestionSeverity,
        row_index: int | None = None,
        column_key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> IngestionIssue:
        return IngestionIssue(
            table_key=self.table_key,
            code=code,
            message=message,
            severity=severity,
            row_index=row_index,
            column_key=column_key,
            context=context or {},
        )

    def make_row_error(
        self,
        row_index: int,
        message: str,
        code: str = "ROW_PARSE_ERROR",
        column_key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> IngestionIssue:
        return self.make_issue(
            code=code,
            message=message,
            severity=IngestionSeverity.ERROR,
            row_index=row_index,
            column_key=column_key,
            context=context,
        )

    def make_issue_from_exception(
        self,
        exc: Exception,
        default_code: str,
        default_message: str,
        severity: IngestionSeverity,
        row_index: int | None = None,
        column_key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> IngestionIssue:
        issue_code = default_code
        issue_message = default_message
        issue_column_key = column_key
        issue_context = dict(context or {})

        if isinstance(exc, UserFacingParseError):
            issue_code = exc.code
            issue_message = exc.message
            issue_column_key = exc.column_key or issue_column_key
            if isinstance(exc.context, dict):
                issue_context.update(exc.context)
        elif isinstance(exc, MappingValidationError):
            issue_code = exc.code
            issue_message = exc.message
            if isinstance(exc.context, dict):
                issue_context.update(exc.context)
        else:
            issue_context.setdefault("exception_type", type(exc).__name__)
            raw_message = str(exc).strip()
            if raw_message:
                issue_context.setdefault("exception_message", raw_message)

        return self.make_issue(
            code=issue_code,
            message=issue_message,
            severity=severity,
            row_index=row_index,
            column_key=issue_column_key,
            context=issue_context,
        )

    def make_row_error_from_exception(
        self,
        row_index: int,
        exc: Exception,
        default_code: str,
        default_message: str,
        column_key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> IngestionIssue:
        return self.make_issue_from_exception(
            exc=exc,
            default_code=default_code,
            default_message=default_message,
            severity=IngestionSeverity.ERROR,
            row_index=row_index,
            column_key=column_key,
            context=context,
        )

    def make_row_warning(
        self,
        row_index: int,
        message: str,
        code: str = "ROW_PARSE_WARNING",
        column_key: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> IngestionIssue:
        return self.make_issue(
            code=code,
            message=message,
            severity=IngestionSeverity.WARNING,
            row_index=row_index,
            column_key=column_key,
            context=context,
        )

    @staticmethod
    def deduplicate_issues(issues: list[IngestionIssue]) -> list[IngestionIssue]:
        unique: dict[tuple, IngestionIssue] = {}
        for issue in issues:
            unique[issue.dedup_key()] = issue
        return list(unique.values())

    def build_result(
        self,
        items: list[T],
        issues: list[IngestionIssue],
        total_rows: int,
        parsed_rows: int,
    ) -> TableParseResult[T]:
        deduped = BaseTableParser.deduplicate_issues(issues)
        skipped_rows = max(total_rows - parsed_rows, 0)
        return TableParseResult(
            table_key=self.table_key,
            items=items,
            issues=deduped,
            total_rows=total_rows,
            parsed_rows=parsed_rows,
            skipped_rows=skipped_rows,
        )
