from __future__ import annotations

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

from application.dto import WorkflowStatus
from .controllers import UiController
from .widgets.table_load_panel import TableLoadPanel


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

        self._refresh_analyze_button_state()

    def _on_schedule_preview_changed(self, df: pd.DataFrame) -> None:
        self._schedule_preview_df = df

    def _refresh_analyze_button_state(self) -> None:
        self._analyze_button.setEnabled(self._controller.can_run_analysis())

    def _on_run_analysis(self) -> None:
        result = self._controller.run_analysis()

        if result.status == WorkflowStatus.FAILED:
            QMessageBox.critical(self, "Chyba analýzy", result.error_message or "Neznámá chyba.")
            return

        if result.status == WorkflowStatus.BLOCKED:
            reasons = result.quality_report.readiness_result.reasons
            message = "\n".join(
                f"- [{reason.severity.value}] {reason.code}: {reason.message_cz}"
                for reason in reasons
            )
            QMessageBox.warning(self, "Analýza zablokována", message or "Analýza je zablokována.")
            return

        errors = result.quality_report.repository_validation_report.errors
        errors_text = ""
        for error in errors:
            errors_text += f"- [{error.severity.value}] {error.code}: {error.message}\n"

        warnings = result.quality_report.repository_validation_report.warnings
        warnings_text = ""
        for warning in warnings:
            warnings_text += f"- [{warning.severity.value}] {warning.code}: {warning.message}\n"

        QMessageBox.information(
            self,
            "Analýza dokončena",
            f"HTML report: {result.html_report_path or 'nevygenerován'}\n"
            f"{errors_text}\n{warnings_text}",
        )