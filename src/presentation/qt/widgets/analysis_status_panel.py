from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.application.dto import AnalyzeWorkflowResult, WorkflowStatus

_DOT_STYLE = "border-radius: 7px; width: 14px; height: 14px; background-color: {color};"


@dataclass(frozen=True, slots=True)
class _UiState:
    text: str
    color: str
    quality_enabled: bool
    report_enabled: bool
    report_in_app_enabled: bool
    schedule_enabled: bool


class AnalysisStatusPanel(QWidget):
    open_quality_requested = Signal()
    open_report_browser_requested = Signal()
    open_report_in_app_requested = Signal()
    open_schedule_violations_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        group = QGroupBox("Výsledek analýzy")
        inner = QVBoxLayout(group)
        inner.setSpacing(8)

        row_top = QHBoxLayout()
        self._dot = QLabel()
        self._dot.setFixedSize(14, 14)
        self._status_text = QLabel("Analýza dosud nebyla spuštěna.")
        row_top.addWidget(self._dot)
        row_top.addWidget(self._status_text, 1)

        self._btn_quality = QPushButton("🧪 Kvalita dat")
        self._btn_quality.clicked.connect(self.open_quality_requested.emit)
        row_top.addWidget(self._btn_quality)
        inner.addLayout(row_top)

        row_reports = QHBoxLayout()
        self._btn_report_browser = QPushButton("🌐 Otevřít zprávu v prohlížeči")
        self._btn_report_browser.clicked.connect(
            self.open_report_browser_requested.emit
        )
        row_reports.addWidget(self._btn_report_browser)

        self._btn_report_app = QPushButton("🖥️ Otevřít zprávu v aplikaci")
        self._btn_report_app.clicked.connect(self.open_report_in_app_requested.emit)
        row_reports.addWidget(self._btn_report_app)
        inner.addLayout(row_reports)

        row_schedule = QHBoxLayout()
        self._btn_schedule = QPushButton("📋 Chyby v rozvrhu")
        self._btn_schedule.clicked.connect(self.open_schedule_violations_requested.emit)
        row_schedule.addWidget(self._btn_schedule)
        inner.addLayout(row_schedule)

        outer = QVBoxLayout(self)
        outer.addWidget(group)

        self.set_initial_state()

    def set_initial_state(self) -> None:
        self._apply(
            _UiState(
                text="Analýza dosud nebyla spuštěna.",
                color="#9E9E9E",
                quality_enabled=False,
                report_enabled=False,
                report_in_app_enabled=False,
                schedule_enabled=False,
            )
        )

    def update_from_result(self, result: AnalyzeWorkflowResult) -> None:
        has_html = bool(result.html_report_path)

        if result.status == WorkflowStatus.SUCCESS:
            self._apply(
                _UiState(
                    text="Analýza byla úspěšně dokončena.",
                    color="#4CAF50",
                    quality_enabled=True,
                    report_enabled=has_html,
                    report_in_app_enabled=has_html,
                    schedule_enabled=True,
                )
            )
            return

        if result.status == WorkflowStatus.BLOCKED:
            self._apply(
                _UiState(
                    text="Analýza je zablokována pravidly připravenosti.",
                    color="#FF9800",
                    quality_enabled=True,
                    report_enabled=False,
                    report_in_app_enabled=False,
                    schedule_enabled=False,
                )
            )
            return

        self._apply(
            _UiState(
                text="Analýza selhala.",
                color="#F44336",
                quality_enabled=True,
                report_enabled=False,
                report_in_app_enabled=False,
                schedule_enabled=False,
            )
        )

    def _apply(self, state: _UiState) -> None:
        self._dot.setStyleSheet(_DOT_STYLE.format(color=state.color))
        self._status_text.setText(state.text)
        self._btn_quality.setEnabled(state.quality_enabled)
        self._btn_report_browser.setEnabled(state.report_enabled)
        self._btn_report_app.setEnabled(state.report_in_app_enabled)
        self._btn_schedule.setEnabled(state.schedule_enabled)
