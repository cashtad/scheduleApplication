from __future__ import annotations

import webbrowser
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.application.dto import WorkflowStatus
from src.presentation.qt.controllers import UiController
from src.presentation.qt.dialogs.data_quality_report_dialog import (
    DataQualityReportDialog,
)

from src.presentation.qt.dialogs.report_viewer_dialog import ReportViewerDialog
from src.presentation.qt.widgets.analysis_status_panel import AnalysisStatusPanel
from src.presentation.qt.widgets.table_load_panel import TableLoadPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Analýza rozvrhu tanečního konkurzu")

        self._controller = UiController(
            rules_config_path=Path("rules_config.yaml"),
            reports_dir=".reports",
            with_html_report_writer=True,
        )
        self._schedule_preview_df: pd.DataFrame | None = None

        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        self._panels: dict[str, TableLoadPanel] = {}
        for table_key in self._controller.required_table_keys():
            panel = TableLoadPanel(
                table_key=table_key,
                controller=self._controller,
                on_schedule_preview_changed=self._on_schedule_preview_changed,
                parent=self,
            )
            panel.status_changed.connect(self._refresh_analyze_button_state)
            self._panels[table_key] = panel
            layout.addWidget(panel)

        actions = QHBoxLayout()
        self._analyze_button = QPushButton("▶ Spustit analýzu")
        self._analyze_button.clicked.connect(self._on_run_analysis)
        actions.addWidget(self._analyze_button)
        layout.addLayout(actions)

        self._analysis_panel = AnalysisStatusPanel(parent=self)
        self._analysis_panel.open_quality_requested.connect(
            self._on_open_quality_report
        )
        self._analysis_panel.open_report_browser_requested.connect(
            self._on_open_report_browser
        )
        self._analysis_panel.open_report_in_app_requested.connect(
            self._on_open_report_in_app
        )
        self._analysis_panel.open_schedule_violations_requested.connect(
            self._on_open_schedule_violations
        )
        layout.addWidget(self._analysis_panel)

        self._refresh_analyze_button_state()

    def _on_schedule_preview_changed(self, df: pd.DataFrame) -> None:
        self._schedule_preview_df = df

    def _refresh_analyze_button_state(self) -> None:
        self._analyze_button.setEnabled(self._controller.can_run_analysis())

    def _on_run_analysis(self) -> None:
        result = self._controller.run_analysis()
        self._analysis_panel.update_from_result(result)

        if result.status == WorkflowStatus.FAILED:
            QMessageBox.critical(
                self, "Chyba analýzy", result.error_message or "Neznámá chyba."
            )
            return

        if result.status == WorkflowStatus.BLOCKED:
            reasons = result.quality_report.readiness_result.reasons
            message = "\n".join(
                f"- [{reason.severity.value}] {reason.code}: {reason.message_cz}"
                for reason in reasons
            )
            QMessageBox.warning(
                self, "Analýza zablokována", message or "Analýza je zablokována."
            )
            return

        QMessageBox.information(
            self,
            "Analýza dokončena",
            f"HTML report: {result.html_report_path or 'nevygenerován'}",
        )

    def _on_open_quality_report(self) -> None:
        report = self._controller.get_last_quality_report()
        if report is None:
            QMessageBox.information(
                self, "Kvalita dat", "Zatím není dostupný žádný report kvality dat."
            )
            return

        dlg = DataQualityReportDialog(report=report, parent=self)
        dlg.exec()

    def _on_open_report_browser(self) -> None:
        report_path = self._controller.get_last_html_report_path()
        if not report_path:
            QMessageBox.information(self, "Report", "HTML report není k dispozici.")
            return
        webbrowser.open(f"file://{report_path}")

    def _on_open_report_in_app(self) -> None:
        report_path = self._controller.get_last_html_report_path()
        if not report_path:
            QMessageBox.information(self, "Report", "HTML report není k dispozici.")
            return
        dlg = ReportViewerDialog(report_path, parent=self)
        dlg.exec()

    def _on_open_schedule_violations(self) -> None:
        QMessageBox.information(
            self,
            "Přehled chyb v rozvrhu",
            "Tato funkce bude doplněna v dalším kroku.",
        )
