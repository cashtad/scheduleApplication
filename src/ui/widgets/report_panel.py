import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.dialogs.report_viewer_dialog import ReportViewerDialog
from src.ui.dialogs.schedule_view_dialog import ScheduleViewDialog


def _format_datetime(path: str) -> str:
    """Extract timestamp from report filename and format it in Czech style."""
    try:
        stem = Path(path).stem  # schedule_report_2026-03-02_14-30
        ts_part = stem.replace("schedule_report_", "")
        dt = datetime.strptime(ts_part, "%Y-%m-%d_%H-%M")
        if sys.platform == "win32":
            return dt.strftime("%#d. %#m. %Y %H:%M")
        return dt.strftime("%-d. %-m. %Y %H:%M")
    except Exception:
        return ""


class ReportPanel(QWidget):
    """Panel shown after a successful analysis with links to the HTML report."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._report_path: str = ""
        self._session = None

        group = QGroupBox("Výsledky analýzy")
        inner = QVBoxLayout(group)

        self._file_label = QLabel()
        self._date_label = QLabel()
        inner.addWidget(self._file_label)
        inner.addWidget(self._date_label)

        btn_row_report = QHBoxLayout()
        self._btn_browser = QPushButton("Otevřít v prohlížeči")
        self._btn_app = QPushButton("Otevřít v aplikaci")
        self._btn_browser.clicked.connect(self._open_in_browser)
        self._btn_app.clicked.connect(self._open_in_app)
        btn_row_report.addWidget(self._btn_browser)
        btn_row_report.addWidget(self._btn_app)
        inner.addLayout(btn_row_report)

        btn_row_table = QHBoxLayout()
        self._show_violations_btn = QPushButton("📋 Zobrazit chyby v tabulce")
        self._show_violations_btn.setEnabled(False)
        self._show_violations_btn.clicked.connect(self._show_violations_table)
        btn_row_table.addWidget(self._show_violations_btn)
        inner.addLayout(btn_row_table)

        outer = QVBoxLayout(self)
        outer.addWidget(group)

    def update_report(self, report_path: str) -> None:
        """Update panel with new report info."""
        self._report_path = report_path
        self._file_label.setText(f"📄 {Path(report_path).name}")
        formatted = _format_datetime(report_path)
        self._date_label.setText(f"Vytvořeno: {formatted}" if formatted else "")
        self._show_violations_btn.setEnabled(True)
        self.show()

    def _open_in_browser(self) -> None:
        webbrowser.open(f"file://{self._report_path}")

    def _open_in_app(self) -> None:
        dlg = ReportViewerDialog(self._report_path, parent=self)
        dlg.exec()

    def _show_violations_table(self) -> None:
        if self._session is None:
            return
        ts = self._session.tables.get("schedule")
        if ts is None or self._session.last_result is None:
            return
        dlg = ScheduleViewDialog(ts.raw_df, self._session.last_result, parent=self)
        dlg.exec()

    def update_session(self, session) -> None:
        """Receive session reference from main window to access tables and results."""
        self._session = session