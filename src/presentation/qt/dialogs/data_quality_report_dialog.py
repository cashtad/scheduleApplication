from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.application.dto import DataQualityReport
from src.ingestion import IngestionIssue

_SEVERITY_FILTER_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Vše", "all"),
    ("Chyby", "error"),
    ("Upozornění", "warning"),
)

_SEVERITY_LABELS_CZ = {
    "error": "chyba",
    "warning": "upozornění",
}

_TABLE_LABELS_CZ = {
    "competitions": "Soutěže",
    "competitors": "Soutěžící",
    "jury": "Porota",
    "schedule": "Rozvrh",
}


class DataQualityReportDialog(QDialog):
    def __init__(self, report: DataQualityReport, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kvalita dat")
        self.resize(980, 700)

        self._report = report

        root = QVBoxLayout(self)

        summary_group = QGroupBox("Souhrn")
        summary_layout = QVBoxLayout(summary_group)

        readiness = report.readiness_result
        decision_text = "POVOLENO ✅" if readiness.is_allowed else "BLOKOVÁNO ❌"
        summary_layout.addWidget(
            QLabel(f"Rozhodnutí připravenosti: <b>{decision_text}</b>")
        )

        summary_layout.addWidget(
            QLabel(
                f"Upozornění (celkem): {report.prepare_data_result.total_warnings_count + len(report.repository_validation_report.warnings)}"
            )
        )

        summary_layout.addWidget(
            QLabel(f"Celkem řádků: {report.prepare_data_result.total_rows}")
        )
        summary_layout.addWidget(
            QLabel(
                f"Chyby řádků: {report.prepare_data_result.total_row_errors_count} "
                f"({report.prepare_data_result.row_error_rate:.1%})"
            )
        )
        summary_layout.addWidget(
            QLabel(f"Chyby schématu: {report.prepare_data_result.schema_errors_count}")
        )

        root.addWidget(summary_group)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filtr závažnosti:"))
        self._severity_filter = QComboBox()
        for label, _ in _SEVERITY_FILTER_OPTIONS:
            self._severity_filter.addItem(label)
        self._severity_filter.currentTextChanged.connect(self._reload_lists)
        filter_row.addWidget(self._severity_filter)
        filter_row.addStretch()
        root.addLayout(filter_row)

        self._tabs = QTabWidget()
        self._readiness_list = QListWidget()
        self._schema_list = QListWidget()
        self._row_list = QListWidget()
        self._repo_list = QListWidget()

        self._tabs.addTab(self._wrap_list(self._readiness_list), "Důvody připravenosti")
        self._tabs.addTab(self._wrap_list(self._repo_list), "Validace repozitáře")
        self._tabs.addTab(self._wrap_list(self._row_list), "Problémy řádků")
        self._tabs.addTab(self._wrap_list(self._schema_list), "Problémy schématu")

        root.addWidget(self._tabs, 1)

        close_btn = QPushButton("Zavřít")
        close_btn.clicked.connect(self.accept)
        root.addWidget(close_btn, alignment=Qt.AlignRight)

        self._reload_lists()

    @staticmethod
    def _wrap_list(list_widget: QListWidget) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(list_widget)
        return w

    def _reload_lists(self) -> None:
        sev = self._selected_severity_value()

        self._fill_readiness(sev)
        self._fill_schema(sev)
        self._fill_row(sev)
        self._fill_repo(sev)

    def _selected_severity_value(self) -> str:
        selected_label = self._severity_filter.currentText()
        for label, value in _SEVERITY_FILTER_OPTIONS:
            if label == selected_label:
                return value
        return "all"

    def _fill_readiness(self, severity_filter: str) -> None:
        self._readiness_list.clear()

        items = []
        for reason in self._report.readiness_result.reasons:
            sev = reason.severity.value
            if severity_filter != "all" and sev != severity_filter:
                continue
            items.append(
                f"[{_SEVERITY_LABELS_CZ.get(sev, sev)}] {reason.code}: {reason.message_cz}"
            )

        self._append_or_empty(self._readiness_list, items)

    def _fill_schema(self, severity_filter: str) -> None:
        self._schema_list.clear()

        items = self._format_ingestion_issues(
            issues=self._report.prepare_data_result.schema_issues,
            severity_filter=severity_filter,
        )
        self._append_or_empty(self._schema_list, items)

    def _fill_row(self, severity_filter: str) -> None:
        self._row_list.clear()

        items = self._format_ingestion_issues(
            issues=self._report.prepare_data_result.row_issues,
            severity_filter=severity_filter,
        )
        self._append_or_empty(self._row_list, items)

    def _fill_repo(self, severity_filter: str) -> None:
        self._repo_list.clear()

        items: list[str] = []
        for issue in self._report.repository_validation_report.errors:
            if severity_filter not in {"all", "error"}:
                continue
            items.append(f"[chyba] {issue.code}: {issue.message}")

        for issue in self._report.repository_validation_report.warnings:
            if severity_filter not in {"all", "warning"}:
                continue
            items.append(f"[upozornění] {issue.code}: {issue.message}")

        self._append_or_empty(self._repo_list, items)

    @staticmethod
    def _format_ingestion_issues(
        issues: Iterable[IngestionIssue],
        severity_filter: str,
    ) -> list[str]:
        rows: list[str] = []
        for issue in issues:
            sev = issue.severity.value
            if severity_filter != "all" and sev != severity_filter:
                continue

            where = _TABLE_LABELS_CZ.get(issue.table_key, issue.table_key)
            if issue.row_index is not None:
                where += f" řádek={issue.row_index}"
            rows.append(
                f"[{_SEVERITY_LABELS_CZ.get(sev, sev)}] {where} | {issue.code}: {issue.message}"
            )
        return rows

    @staticmethod
    def _append_or_empty(list_widget: QListWidget, lines: list[str]) -> None:
        if not lines:
            list_widget.addItem(QListWidgetItem("Žádné položky pro zvolený filtr."))
            return
        for line in lines:
            list_widget.addItem(QListWidgetItem(line))
