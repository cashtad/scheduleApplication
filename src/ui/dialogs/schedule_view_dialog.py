import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QTableView,
    QVBoxLayout,
)

from src.expert_system.rules import Severity
from src.expert_system.inference_engine import ScheduleAnalysisResult


SEVERITY_BG = {
    Severity.CRITICAL: QColor("#FFCDD2"),  # light red
    Severity.MEDIUM:   QColor("#FFE0B2"),  # light orange
    Severity.LOW:      QColor("#FFF9C4"),  # light yellow
}

SEVERITY_LABELS = {
    Severity.CRITICAL: "🔴 KRITICKÉ",
    Severity.MEDIUM:   "🟡 STŘEDNÍ",
    Severity.LOW:      "🟢 NÍZKÉ",
}

_DEFAULT_BG = QColor("#FFFFFF")
_DEFAULT_FG = QColor("#000000")


def _severity_rank(s: Severity) -> int:
    return {Severity.CRITICAL: 3, Severity.MEDIUM: 2, Severity.LOW: 1}.get(s, 0)


class ScheduleViewDialog(QDialog):
    """Dialog showing the schedule DataFrame with rows highlighted by violation severity."""

    def __init__(self, df: pd.DataFrame, result: ScheduleAnalysisResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přehled chyb v rozvrhu")
        self.resize(1100, 650)

        layout = QVBoxLayout(self)

        # Legend
        legend = QLabel(
            "  🔴 Červená = KRITICKÉ nárušení   "
            "🟡 Oranžová = STŘEDNÍ nárušení   "
            "🟢 Žlutá = NÍZKÉ nárušení   "
            "  Bílá = bez nárušení"
        )
        legend.setWordWrap(True)
        layout.addWidget(legend)

        # Build row_index → worst Severity mapping
        row_severity: dict[int, Severity] = {}
        for violation in result.violations:
            for row_idx in violation.source_rows:
                existing = row_severity.get(row_idx)
                if existing is None or _severity_rank(violation.severity) > _severity_rank(existing):
                    row_severity[row_idx] = violation.severity

        # Build row_index → violation descriptions for tooltip
        row_descriptions: dict[int, list[str]] = {}
        for violation in result.violations:
            for row_idx in violation.source_rows:
                row_descriptions.setdefault(row_idx, []).append(
                    f"[{SEVERITY_LABELS[violation.severity]}] {violation.description}"
                )

        # Build model
        model = QStandardItemModel(len(df), len(df.columns))
        model.setHorizontalHeaderLabels(list(df.columns))
        model.setVerticalHeaderLabels([str(i) for i in df.index])

        for r, (df_idx, row_data) in enumerate(df.iterrows()):
            severity = row_severity.get(df_idx)
            bg = SEVERITY_BG.get(severity, _DEFAULT_BG)
            tooltip = "\n".join(row_descriptions.get(df_idx, []))

            for c, val in enumerate(row_data):
                item = QStandardItem(str(val))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setBackground(bg)
                item.setForeground(_DEFAULT_FG)
                if tooltip:
                    item.setToolTip(tooltip)
                model.setItem(r, c, item)

        table = QTableView()
        table.setModel(model)
        table.resizeColumnsToContents()
        layout.addWidget(table)

        # Summary line
        n_rows = len(row_severity)
        n_critical = sum(1 for s in row_severity.values() if s == Severity.CRITICAL)
        n_medium = sum(1 for s in row_severity.values() if s == Severity.MEDIUM)
        n_low = sum(1 for s in row_severity.values() if s == Severity.LOW)
        summary = QLabel(
            f"Celkem řádků s nárušeními: {n_rows}  "
            f"(🔴 {n_critical} kritických, 🟡 {n_medium} středních, 🟢 {n_low} nízkých)"
        )
        layout.addWidget(summary)
