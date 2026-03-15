from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
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

    Clicking a row that belongs to one or more violations shows a right-side panel
    listing all violations for that row.  Each violation has a *Highlight rows* button
    that applies a blue tint to all rows belonging to that violation.  Clicking a row
    without violations hides the panel and clears any active highlight.
    """

    def __init__(self, df: pd.DataFrame, result: ScheduleAnalysisResult, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Přehled chyb v rozvrhu")
        self.resize(1300, 700)

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

        # Right-side violation panel (hidden by default)
        self._violation_panel, self._violation_panel_layout = self._build_violation_panel()
        self._panel_scroll = QScrollArea()
        self._panel_scroll.setWidget(self._violation_panel)
        self._panel_scroll.setWidgetResizable(True)
        self._panel_scroll.setMinimumWidth(340)
        self._panel_scroll.setMaximumWidth(500)
        self._panel_scroll.hide()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._table)
        splitter.addWidget(self._panel_scroll)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

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
        legend.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
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

    @staticmethod
    def _build_violation_panel() -> tuple[QWidget, QVBoxLayout]:
        """Create the right-side violation panel container (initially empty)."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        return container, layout

    def _build_violation_card(self, violation: Violation) -> QFrame:
        """Build a single violation card widget with all relevant information."""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setFrameShadow(QFrame.Raised)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)

        # Severity + rule name header
        header_label = QLabel(
            f"<b>{SEVERITY_LABELS[violation.severity]}</b>"
            f"  —  <i>{violation.rule_name}</i>"
        )
        header_label.setWordWrap(True)
        card_layout.addWidget(header_label)

        # Entity info
        entity_label = QLabel(f"Subjekt: <b>{violation.entity_name}</b> ({violation.entity_id})")
        entity_label.setWordWrap(True)
        card_layout.addWidget(entity_label)

        # Description
        desc_label = QLabel(violation.description)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        # Details section
        if violation.details:
            details_lines = [
                f"<b>Podrobnosti:</b>"
            ]
            for key, value in violation.details.items():
                details_lines.append(f"  • {key}: {value}")
            details_label = QLabel("<br>".join(details_lines))
            details_label.setWordWrap(True)
            details_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            card_layout.addWidget(details_label)

        # Highlight button
        highlight_btn = QPushButton("🔵 Vybrat řádky")
        highlight_btn.setToolTip(
            f"Zvýrazní všechny řádky ({len(violation.source_rows)}) patřící k tomuto narušení"
        )
        highlight_btn.clicked.connect(lambda: self._apply_highlight(violation))
        card_layout.addWidget(highlight_btn)

        return card

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
    # Right-panel helpers
    # ------------------------------------------------------------------

    def _populate_violation_panel(self, violations: list[Violation]) -> None:
        """Clear and repopulate the right panel with cards for each violation."""
        # Remove all existing widgets from the panel layout
        while self._violation_panel_layout.count():
            child = self._violation_panel_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        title = QLabel(f"<b>Narušení pro tento řádek ({len(violations)})</b>")
        title.setWordWrap(True)
        self._violation_panel_layout.addWidget(title)

        for violation in violations:
            card = self._build_violation_card(violation)
            self._violation_panel_layout.addWidget(card)

        self._panel_scroll.show()

    def _hide_violation_panel(self) -> None:
        """Hide the right panel and remove its content."""
        self._panel_scroll.hide()
        while self._violation_panel_layout.count():
            child = self._violation_panel_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    # ------------------------------------------------------------------
    # Interaction handlers
    # ------------------------------------------------------------------

    def _on_row_clicked(self, index) -> None:
        model_row = index.row()
        df_idx    = self._model_row_to_df_idx[model_row]
        violations = self._row_to_violations.get(df_idx, [])

        if not violations:
            # Row has no violations – clear selection and hide panel
            self._clear_highlight()
            return

        self._populate_violation_panel(violations)

    def _apply_highlight(self, violation: Violation) -> None:
        """Highlight all rows belonging to *violation*, restore all other rows."""
        self._highlighted_violation = violation
        highlighted_rows = set(violation.source_rows)

        for model_row, df_idx in enumerate(self._model_row_to_df_idx):
            self._refresh_row(model_row, df_idx, highlighted=df_idx in highlighted_rows)

    def _clear_highlight(self) -> None:
        """Remove the violation highlight, restore severity-based colouring, and hide the panel."""
        self._hide_violation_panel()
        if self._highlighted_violation is None:
            return
        prev = self._highlighted_violation
        self._highlighted_violation = None
        for df_idx in prev.source_rows:
            model_row = self._df_idx_to_model_row.get(df_idx)
            if model_row is not None:
                self._refresh_row(model_row, df_idx, highlighted=False)