from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from expert_system import ScheduleAnalysisResult, Severity
from expert_system.rules import Violation

SEVERITY_BG = {
    Severity.CRITICAL: QColor("#FFCDD2"),  # light red
    Severity.MEDIUM:   QColor("#FFE0B2"),  # light orange
    Severity.LOW:      QColor("#FFF9C4"),  # light yellow
}

# Highlight tint applied on top of severity colour when a violation is selected
_HIGHLIGHT_BG = QColor("#B3E5FC")  # light blue – works in both light and dark themes

SEVERITY_LABELS = {
    Severity.CRITICAL: "🔴 KRITICKÉ",
    Severity.MEDIUM:   "🟡 STŘEDNÍ",
    Severity.LOW:      "🟢 NÍZKÉ",
}

_DEFAULT_BG = QColor("#FFFFFF")
_DEFAULT_FG = QColor("#000000")

_SEVERITY_RANK = {Severity.CRITICAL: 3, Severity.MEDIUM: 2, Severity.LOW: 1}


class ScheduleViewDialog(QDialog):
    """Dialog showing the schedule DataFrame with rows highlighted by violation severity.

    Clicking a row that belongs to one or more violations highlights all rows for
    that violation in a distinct blue tint.  If a row is part of multiple violations
    the user is asked to choose which one to highlight.  Clicking a row without any
    violation (or pressing the *Clear selection* button) removes the highlight.
    """

    def __init__(self, df: pd.DataFrame, result: ScheduleAnalysisResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přehled chyb v rozvrhu")
        self.resize(1100, 650)

        self._df = df
        self._result = result

        # Pre-computed maps
        self._row_severity    = self._build_row_severity_map(result)
        self._row_descriptions = self._build_row_descriptions_map(result)
        self._row_to_violations: dict[int, list[Violation]] = self._build_row_to_violations(result)

        # model row index (0-based) → DataFrame index value  and reverse
        self._model_row_to_df_idx: list[int] = [int(idx) for idx in df.index]
        self._df_idx_to_model_row: dict[int, int] = {
            df_idx: model_row
            for model_row, df_idx in enumerate(self._model_row_to_df_idx)
        }

        # Currently highlighted violation (or None)
        self._highlighted_violation: Violation | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(self._build_legend())

        self._model = QStandardItemModel(len(df), len(df.columns))
        self._table = self._build_table()
        layout.addWidget(self._table)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self._build_summary_label(self._row_severity))
        bottom_layout.addStretch()
        clear_btn = QPushButton("Zrušit výběr")
        clear_btn.setToolTip("Zruší zvýraznění vybraného narušení")
        clear_btn.clicked.connect(self._clear_highlight)
        bottom_layout.addWidget(clear_btn)
        layout.addLayout(bottom_layout)

        # Connect row-click signal
        self._table.clicked.connect(self._on_row_clicked)

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

    @staticmethod
    def _build_row_to_violations(result: ScheduleAnalysisResult) -> dict[int, list[Violation]]:
        """Map each source row index to the list of Violation objects that involve it."""
        mapping: dict[int, list[Violation]] = {}
        for violation in result.violations:
            for row_idx in violation.source_rows:
                mapping.setdefault(row_idx, []).append(violation)
        return mapping

    # ------------------------------------------------------------------
    # Widget builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_legend() -> QLabel:
        legend = QLabel(
            "  🔴 Červená = KRITICKÉ narušení   "
            "🟡 Oranžová = STŘEDNÍ narušení   "
            "🟢 Žlutá = NÍZKÉ narušení   "
            "  Bílá = bez narušení   "
            "  🔵 Modrá = vybrané narušení"
        )
        legend.setWordWrap(True)
        return legend

    def _build_table(self) -> QTableView:
        df = self._df
        self._model.setHorizontalHeaderLabels(list(df.columns))
        self._model.setVerticalHeaderLabels([str(i) for i in df.index])

        for r, (df_idx, _) in enumerate(df.iterrows()):
            self._refresh_row(r, int(df_idx), highlighted=False)

        table = QTableView()
        table.setModel(self._model)
        table.resizeColumnsToContents()
        return table

    def _build_summary_label(self, row_severity: dict[int, Severity]) -> QLabel:
        severities   = list(row_severity.values())
        n_rows     = len(severities)
        n_critical = severities.count(Severity.CRITICAL)
        n_medium   = severities.count(Severity.MEDIUM)
        n_low      = severities.count(Severity.LOW)
        return QLabel(
            f"Celkem řádků s narušeními: {n_rows}  "
            f"(🔴 {n_critical} kritických, 🟡 {n_medium} středních, 🟢 {n_low} nízkých)"
        )

    # ------------------------------------------------------------------
    # Row styling helpers
    # ------------------------------------------------------------------

    def _refresh_row(self, model_row: int, df_idx: int, *, highlighted: bool) -> None:
        """Set the visual style of a single model row."""
        severity = self._row_severity.get(df_idx)
        base_bg  = SEVERITY_BG.get(severity, _DEFAULT_BG)
        bg       = _HIGHLIGHT_BG if highlighted else base_bg

        selected_violation = self._highlighted_violation
        raw_descs = self._row_descriptions.get(df_idx, [])

        if highlighted and selected_violation is not None:
            # Mark the selected violation in the tooltip
            label = SEVERITY_LABELS[selected_violation.severity]
            selected_line = f"[{label}] {selected_violation.description}"
            tooltip_lines = [
                (f"► {d}  ← VYBRANÉ" if d == selected_line else d)
                for d in raw_descs
            ]
        else:
            tooltip_lines = raw_descs

        tooltip = "\n".join(tooltip_lines)

        bold_font = QFont()
        bold_font.setBold(highlighted)

        for c in range(self._model.columnCount()):
            item = self._model.item(model_row, c)
            if item is None:
                row_data = list(self._df.loc[df_idx])
                item = QStandardItem(str(row_data[c]))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self._model.setItem(model_row, c, item)
            item.setBackground(bg)
            item.setForeground(_DEFAULT_FG)
            item.setFont(bold_font)
            item.setToolTip(tooltip)

    # ------------------------------------------------------------------
    # Interaction handlers
    # ------------------------------------------------------------------

    def _on_row_clicked(self, index) -> None:
        model_row = index.row()
        df_idx    = self._model_row_to_df_idx[model_row]
        violations = self._row_to_violations.get(df_idx, [])

        if not violations:
            # Row has no violations – clear selection
            self._clear_highlight()
            return

        if len(violations) == 1:
            chosen = violations[0]
        else:
            # Ask the user which violation to highlight
            choices = [
                f"{SEVERITY_LABELS[v.severity]}: {v.description}"
                for v in violations
            ]
            item, ok = QInputDialog.getItem(
                self,
                "Vyberte narušení",
                "Tento řádek patří do více narušení.\nVyberte, které chcete zvýraznit:",
                choices,
                current=0,
                editable=False,
            )
            if not ok:
                return
            chosen = violations[choices.index(item)]

        self._apply_highlight(chosen)

    def _apply_highlight(self, violation: Violation) -> None:
        """Highlight all rows belonging to *violation*, restore all other rows."""
        self._highlighted_violation = violation
        highlighted_rows = set(violation.source_rows)

        for model_row, df_idx in enumerate(self._model_row_to_df_idx):
            self._refresh_row(model_row, df_idx, highlighted=df_idx in highlighted_rows)

    def _clear_highlight(self) -> None:
        """Remove the violation highlight and restore severity-based colouring."""
        if self._highlighted_violation is None:
            return
        prev = self._highlighted_violation
        self._highlighted_violation = None
        for df_idx in prev.source_rows:
            model_row = self._df_idx_to_model_row.get(df_idx)
            if model_row is not None:
                self._refresh_row(model_row, df_idx, highlighted=False)