import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QDialog, QLabel, QTableView, QVBoxLayout

from expert_system import ScheduleAnalysisResult, Severity

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

_SEVERITY_RANK = {Severity.CRITICAL: 3, Severity.MEDIUM: 2, Severity.LOW: 1}


class ScheduleViewDialog(QDialog):
    """Dialog showing the schedule DataFrame with rows highlighted by violation severity."""

    def __init__(self, df: pd.DataFrame, result: ScheduleAnalysisResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přehled chyb v rozvrhu")
        self.resize(1100, 650)

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_legend())

        row_severity    = self._build_row_severity_map(result)
        row_descriptions = self._build_row_descriptions_map(result)

        layout.addWidget(self._build_table(df, row_severity, row_descriptions))
        layout.addWidget(self._build_summary_label(row_severity))

    # ------------------------------------------------------------------
    # Data preparation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_row_severity_map(result: ScheduleAnalysisResult) -> dict[int, Severity]:
        """Map each source row index to the worst Severity among its violations."""
        row_severity: dict[int, Severity] = {}
        for violation in result.violations:
            for row_idx in violation.source_rows:
                existing = row_severity.get(row_idx)
                if existing is None or _SEVERITY_RANK[violation.severity] > _SEVERITY_RANK[existing]:
                    row_severity[row_idx] = violation.severity
        return row_severity

    @staticmethod
    def _build_row_descriptions_map(result: ScheduleAnalysisResult) -> dict[int, list[str]]:
        """Map each source row index to a list of human-readable violation descriptions."""
        row_descriptions: dict[int, list[str]] = {}
        for violation in result.violations:
            label = SEVERITY_LABELS[violation.severity]
            for row_idx in violation.source_rows:
                row_descriptions.setdefault(row_idx, []).append(
                    f"[{label}] {violation.description}"
                )
        return row_descriptions

    # ------------------------------------------------------------------
    # Widget builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_legend() -> QLabel:
        legend = QLabel(
            "  🔴 Červená = KRITICKÉ narušení   "
            "🟡 Oranžová = STŘEDNÍ narušení   "
            "🟢 Žlutá = NÍZKÉ narušení   "
            "  Bílá = bez narušení"
        )
        legend.setWordWrap(True)
        return legend

    @staticmethod
    def _build_table(
        df: pd.DataFrame,
        row_severity: dict[int, Severity],
        row_descriptions: dict[int, list[str]],
    ) -> QTableView:
        model = QStandardItemModel(len(df), len(df.columns))
        model.setHorizontalHeaderLabels(list(df.columns))
        model.setVerticalHeaderLabels([str(i) for i in df.index])

        for r, (df_idx, row_data) in enumerate(df.iterrows()):
            severity = row_severity.get(df_idx)
            bg       = SEVERITY_BG.get(severity, _DEFAULT_BG)
            tooltip  = "\n".join(row_descriptions.get(df_idx, []))

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
        return table

    @staticmethod
    def _build_summary_label(row_severity: dict[int, Severity]) -> QLabel:
        severities   = list(row_severity.values())
        n_rows     = len(severities)
        n_critical = severities.count(Severity.CRITICAL)
        n_medium   = severities.count(Severity.MEDIUM)
        n_low      = severities.count(Severity.LOW)
        return QLabel(
            f"Celkem řádků s narušeními: {n_rows}  "
            f"(🔴 {n_critical} kritických, 🟡 {n_medium} středních, 🟢 {n_low} nízkých)"
        )