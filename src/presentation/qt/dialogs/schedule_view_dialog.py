from __future__ import annotations

from datetime import datetime

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

from src.application.dto import AnalysisViewModel, ViolationViewItem

_SEVERITY_BG = {
    "critical": QColor("#FFCDD2"),
    "medium": QColor("#FFE0B2"),
    "low": QColor("#C8E6C9"),
}
_SEVERITY_LABELS = {
    "critical": "🔴 KRITICKÉ",
    "medium": "🟡 STŘEDNÍ",
    "low": "🟢 NÍZKÉ",
}
_HIGHLIGHT_BG = QColor("#B3E5FC")
_DEFAULT_BG = QColor("#FFFFFF")
_DEFAULT_FG = QColor("#000000")
_SEVERITY_RANK = {"critical": 3, "medium": 2, "low": 1}


class ScheduleViewDialog(QDialog):
    def __init__(
        self,
        schedule_df: pd.DataFrame,
        analysis_view: AnalysisViewModel,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Přehled chyb v rozvrhu")
        self.resize(1300, 760)

        self._df = schedule_df
        self._analysis_view = analysis_view

        self._violations_by_id: dict[str, ViolationViewItem] = {
            v.violation_id: v for v in analysis_view.violations
        }
        self._row_to_violation_ids = dict(analysis_view.row_to_violation_ids)
        self._row_to_severity = self._build_row_severity_map()

        self._model_row_to_df_idx: list[int] = [int(idx) for idx in schedule_df.index]
        self._df_idx_to_model_row: dict[int, int] = {
            df_idx: model_row
            for model_row, df_idx in enumerate(self._model_row_to_df_idx)
        }

        self._highlighted_violation_id: str | None = None

        root = QVBoxLayout(self)
        root.addWidget(self._build_legend())

        self._model = QStandardItemModel(len(schedule_df), len(schedule_df.columns))
        self._table = self._build_table()

        self._panel_container, self._panel_layout = self._build_violation_panel()
        self._panel_scroll = QScrollArea()
        self._panel_scroll.setWidget(self._panel_container)
        self._panel_scroll.setWidgetResizable(True)
        self._panel_scroll.setMinimumWidth(360)
        self._panel_scroll.setMaximumWidth(520)
        self._panel_scroll.hide()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._table)
        splitter.addWidget(self._panel_scroll)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        bottom.addWidget(self._build_summary_label())
        bottom.addStretch()
        root.addLayout(bottom)

        self._table.clicked.connect(self._on_row_clicked)

    def _build_row_severity_map(self) -> dict[int, str]:
        row_to_severity: dict[int, str] = {}
        for row_idx, violation_ids in self._row_to_violation_ids.items():
            worst = "low"
            for violation_id in violation_ids:
                v = self._violations_by_id.get(violation_id)
                if v is None:
                    continue
                if _SEVERITY_RANK.get(v.severity, 0) > _SEVERITY_RANK.get(worst, 0):
                    worst = v.severity
            row_to_severity[row_idx] = worst
        return row_to_severity

    def _build_legend(self) -> QLabel:
        legend = QLabel(
            "🔴 Kritické   🟡 Střední   🟢 Nízké   "
            "⚪ Bez narušení   🔵 Vybrané narušení"
        )
        legend.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        return legend

    def _build_table(self) -> QTableView:
        df = self._df
        self._model.setHorizontalHeaderLabels([str(c) for c in df.columns])
        self._model.setVerticalHeaderLabels([str(i) for i in df.index])

        for model_row, (df_idx, _) in enumerate(df.iterrows()):
            self._refresh_row(model_row, int(df_idx), highlighted=False)

        table = QTableView()
        table.setModel(self._model)
        table.resizeColumnsToContents()
        return table

    def _build_summary_label(self) -> QLabel:
        severities = list(self._row_to_severity.values())
        total = len(severities)
        critical = severities.count("critical")
        medium = severities.count("medium")
        low = severities.count("low")
        return QLabel(
            f"Řádky s narušeními: {total}  (🔴 {critical}, 🟡 {medium}, 🟢 {low})"
        )

    @staticmethod
    def _build_violation_panel() -> tuple[QWidget, QVBoxLayout]:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        return container, layout

    def _build_violation_card(self, violation: ViolationViewItem) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setFrameShadow(QFrame.Raised)

        lay = QVBoxLayout(card)
        lay.setSpacing(4)

        header = QLabel(
            f"<b>{_SEVERITY_LABELS.get(violation.severity, violation.severity)}</b>"
            f" — <i>{violation.rule_name}</i>"
        )
        header.setWordWrap(True)
        lay.addWidget(header)

        entity = QLabel(f"Subjekt: <b>{violation.entity_name}</b>")
        entity.setWordWrap(True)
        lay.addWidget(entity)

        desc = QLabel(violation.description)
        desc.setWordWrap(True)
        lay.addWidget(desc)

        if violation.details:
            detail_lines = ["<b>Podrobnosti:</b>"]
            for key, value in violation.details.items():
                if isinstance(value, datetime):
                    value = value.strftime("%H:%M")
                detail_lines.append(f"• {key}: {value}")
            details = QLabel("<br>".join(detail_lines))
            details.setWordWrap(True)
            details.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lay.addWidget(details)

        btn = QPushButton("🔵 Vybrat řádky")
        btn.clicked.connect(lambda: self._apply_highlight(violation.violation_id))
        lay.addWidget(btn)

        return card

    def _refresh_row(self, model_row: int, df_idx: int, *, highlighted: bool) -> None:
        severity = self._row_to_severity.get(df_idx)
        base_bg = _SEVERITY_BG.get(severity, _DEFAULT_BG)
        bg = _HIGHLIGHT_BG if highlighted else base_bg

        tooltip = "\n".join(self._tooltip_lines_for_row(df_idx, highlighted))

        font = QFont()
        font.setBold(highlighted)

        for c in range(self._model.columnCount()):
            item = self._model.item(model_row, c)
            if item is None:
                row_data = list(self._df.loc[df_idx])
                item = QStandardItem(str(row_data[c]))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self._model.setItem(model_row, c, item)

            item.setBackground(bg)
            item.setForeground(_DEFAULT_FG)
            item.setFont(font)
            item.setToolTip(tooltip)

    def _tooltip_lines_for_row(self, df_idx: int, highlighted: bool) -> list[str]:
        violation_ids = self._row_to_violation_ids.get(df_idx, [])
        lines: list[str] = []

        for violation_id in violation_ids:
            v = self._violations_by_id.get(violation_id)
            if v is None:
                continue
            label = _SEVERITY_LABELS.get(v.severity, v.severity)
            line = f"[{label}] {v.description}"
            if highlighted and self._highlighted_violation_id == violation_id:
                line += "  ← VYBRANÉ"
            lines.append(line)

        return lines

    def _populate_violation_panel(self, violations: list[ViolationViewItem]) -> None:
        while self._panel_layout.count():
            child = self._panel_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        title = QLabel(f"<b>Narušení pro tento řádek ({len(violations)})</b>")
        title.setWordWrap(True)
        self._panel_layout.addWidget(title)

        violations = sorted(
            violations,
            key=lambda v: _SEVERITY_RANK.get(v.severity, 0),
            reverse=True,
        )
        for violation in violations:
            self._panel_layout.addWidget(self._build_violation_card(violation))

        clear_btn = QPushButton("Zrušit výběr")
        clear_btn.clicked.connect(self._clear_highlight)
        self._panel_layout.addWidget(clear_btn)

        self._panel_scroll.show()

    def _hide_violation_panel(self) -> None:
        self._panel_scroll.hide()
        while self._panel_layout.count():
            child = self._panel_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _on_row_clicked(self, index) -> None:
        model_row = index.row()
        df_idx = self._model_row_to_df_idx[model_row]
        violation_ids = self._row_to_violation_ids.get(df_idx, [])

        if not violation_ids:
            self._clear_highlight()
            return

        violations = [
            self._violations_by_id[vid]
            for vid in violation_ids
            if vid in self._violations_by_id
        ]
        self._populate_violation_panel(violations)

    def _apply_highlight(self, violation_id: str) -> None:
        violation = self._violations_by_id.get(violation_id)
        if violation is None:
            return

        self._highlighted_violation_id = violation_id
        highlighted_rows = set(violation.source_rows)

        for model_row, df_idx in enumerate(self._model_row_to_df_idx):
            self._refresh_row(
                model_row, df_idx, highlighted=(df_idx in highlighted_rows)
            )

    def _clear_highlight(self) -> None:
        self._hide_violation_panel()
        if self._highlighted_violation_id is None:
            return

        self._highlighted_violation_id = None
        for model_row, df_idx in enumerate(self._model_row_to_df_idx):
            self._refresh_row(model_row, df_idx, highlighted=False)
