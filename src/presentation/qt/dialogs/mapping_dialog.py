from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

_MAPPING_HIGHLIGHT_COLORS = [
    QColor("#BBDEFB"),  # light blue
    QColor("#C8E6C9"),  # light green
    QColor("#FFE0B2"),  # light orange
    QColor("#F8BBD9"),  # light pink
    QColor("#E1BEE7"),  # light purple
    QColor("#B2EBF2"),  # light cyan
    QColor("#FFF9C4"),  # light yellow
]
_MAPPING_DEFAULT_BG = QColor("#FFFFFF")
_MAPPING_DEFAULT_FG = QColor("#000000")
_MAPPING_HIGHLIGHT_FG = QColor("#000000")

_PREFIX_RE = re.compile(r"^(.*?)(\d+)$")


@dataclass(frozen=True, slots=True)
class MappingField:
    key: str
    label: str
    required: bool = True


TABLE_MAPPING_FIELDS: dict[str, list[MappingField]] = {
    "competitions": [
        MappingField("id", "ID soutěže", True),
        MappingField("name", "Název", True),
        MappingField("discipline", "Disciplína", True),
        MappingField("amount_of_rounds", "Počet kol", True)
    ],
    "competitors": [
        MappingField("p1_name_surname", "Jméno závodníka 1", True),
        MappingField("p2_name_surname", "Jméno závodníka 2", False),
        MappingField("count", "Počet závodníků páru", True),
        MappingField("assignment_prefix", "Prefix pro ID soutěží (např. '#')", True),

    ],
    "jury": [
        MappingField("name", "Jméno", False),
        MappingField("surname", "Příjmení", True),
        MappingField("assignment_prefix", "Prefix pro ID soutěží (např. '#')", True),
    ],
    "schedule": [
        MappingField("competition_id", "ID soutěže", True),
        MappingField("start_time", "Začátek", True),
        MappingField("end_time", "Konec", True),
    ],
}


class MappingDialog(QDialog):
    def __init__(
        self,
        table_key: str,
        df: pd.DataFrame,
        existing_mapping: Optional[dict[str, str]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mapování sloupců")
        self.resize(950, 620)

        self._table_key = table_key
        self._df = df
        self._fields = TABLE_MAPPING_FIELDS.get(table_key, [])

        self._combos: dict[str, QComboBox] = {}
        self._line_edits: dict[str, QLineEdit] = {}
        self._prefix_hint_labels: dict[str, QLabel] = {}
        self._field_to_selected_value: dict[str, str] = {}

        self.result_mapping: dict[str, str] = {}

        root = QVBoxLayout(self)

        instruction = QLabel(
            "Vyberte sloupce pro jednotlivá pole. "
            "Zvolený sloupec se okamžitě zvýrazní v tabulce."
        )
        root.addWidget(instruction)

        self._model = QStandardItemModel(len(df), len(df.columns))
        self._model.setHorizontalHeaderLabels([str(c) for c in df.columns])
        self._model.setVerticalHeaderLabels([str(i + 1) for i in range(len(df))])

        for row_idx, row in enumerate(df.itertuples(index=False)):
            for col_idx, value in enumerate(row):
                item = QStandardItem(str(value))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setBackground(_MAPPING_DEFAULT_BG)
                item.setForeground(_MAPPING_DEFAULT_FG)
                self._model.setItem(row_idx, col_idx, item)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.resizeColumnsToContents()
        root.addWidget(self._table)

        group = QGroupBox("Mapování polí")
        form = QFormLayout(group)
        columns = [str(c) for c in df.columns]

        for field in self._fields:
            existing_value = (existing_mapping or {}).get(field.key, "")
            display_label = f"{field.label} *" if field.required else field.label
            field_color = self._field_color(field.key)

            if field.key.endswith("_prefix"):
                inner = self._build_prefix_editor(field.key, existing_value)
                form.addRow(display_label, self._wrap_with_swatch(field_color, inner))
            else:
                combo = QComboBox()
                if not field.required:
                    combo.addItem("")
                combo.addItems(columns)

                if existing_value:
                    idx = combo.findText(existing_value)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)

                combo.currentTextChanged.connect(
                    lambda text, fk=field.key: self._on_combo_value_changed(fk, text)
                )
                self._combos[field.key] = combo
                form.addRow(display_label, self._wrap_with_swatch(field_color, combo))

        root.addWidget(group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Potvrdit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if existing_mapping:
            for field in self._fields:
                if field.key in existing_mapping:
                    self._field_to_selected_value[field.key] = existing_mapping[field.key]

        for field in self._fields:
            if field.key.endswith("_prefix"):
                self._update_prefix_hint(field.key, self._field_to_selected_value.get(field.key, ""))

        self._refresh_highlights()

    def _build_prefix_editor(self, field_key: str, existing_value: str) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        line_edit = QLineEdit(existing_value)
        line_edit.textChanged.connect(
            lambda text, fk=field_key: self._on_prefix_value_changed(fk, text)
        )
        self._line_edits[field_key] = line_edit
        row.addWidget(line_edit)

        detect_btn = QPushButton("Najít automaticky")
        detect_btn.clicked.connect(lambda _=False, fk=field_key: self._auto_detect_prefix(fk))
        row.addWidget(detect_btn)

        hint = QLabel("→ 0 sloupců")
        self._prefix_hint_labels[field_key] = hint
        row.addWidget(hint)

        return container

    def _field_color(self, field_key: str) -> QColor:
        for idx, field in enumerate(self._fields):
            if field.key == field_key:
                return _MAPPING_HIGHLIGHT_COLORS[idx % len(_MAPPING_HIGHLIGHT_COLORS)]
        return _MAPPING_HIGHLIGHT_COLORS[0]

    @staticmethod
    def _wrap_with_swatch(color: QColor, inner: QWidget) -> QWidget:
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        swatch = QLabel()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #888; border-radius: 2px;"
        )

        row.addWidget(swatch)
        row.addWidget(inner, stretch=1)
        return container

    def _on_combo_value_changed(self, field_key: str, value: str) -> None:
        self._field_to_selected_value[field_key] = value
        self._refresh_highlights()

    def _on_prefix_value_changed(self, field_key: str, value: str) -> None:
        self._field_to_selected_value[field_key] = value
        self._update_prefix_hint(field_key, value)
        self._refresh_highlights()

    def _auto_detect_prefix(self, field_key: str) -> None:
        groups: dict[str, list[int]] = {}
        for col in [str(c) for c in self._df.columns]:
            match = _PREFIX_RE.match(col)
            if not match:
                continue
            prefix, num = match.group(1), int(match.group(2))
            groups.setdefault(prefix, []).append(num)

        candidates: list[tuple[str, int]] = []
        for prefix, numbers in groups.items():
            values = sorted(numbers)
            n = len(values)
            if n >= 2 and values == list(range(1, n + 1)):
                candidates.append((prefix, n))

        if not candidates:
            QMessageBox.information(
                self,
                "Automatická detekce",
                "Prefix se nepodařilo detekovat. Zadejte jej ručně.",
            )
            return

        if len(candidates) == 1:
            self._line_edits[field_key].setText(candidates[0][0])
            return

        labels = [
            f"{prefix or 'bez prefixu'} ({count} sloupců)"
            for prefix, count in candidates
        ]
        selected, ok = QInputDialog.getItem(
            self,
            "Vyberte prefix",
            "Nalezeno více kandidátů. Vyberte prefix:",
            labels,
            0,
            False,
        )
        if not ok or not selected:
            return

        idx = labels.index(selected)
        self._line_edits[field_key].setText(candidates[idx][0])

    def _update_prefix_hint(self, field_key: str, prefix: str) -> None:
        label = self._prefix_hint_labels.get(field_key)
        if label is None:
            return

        columns = [str(c) for c in self._df.columns]
        if prefix == "":
            matched = [c for c in columns if self._is_int_column_name(c)]
        else:
            matched = [c for c in columns if c.startswith(prefix)]

        label.setText(f"→ {len(matched)} sloupců")

    @staticmethod
    def _is_int_column_name(text: str) -> bool:
        try:
            int(text)
            return True
        except (TypeError, ValueError):
            return False

    def _refresh_highlights(self) -> None:
        rows = self._model.rowCount()
        cols = self._model.columnCount()
        columns = [str(c) for c in self._df.columns]

        for r in range(rows):
            for c in range(cols):
                item = self._model.item(r, c)
                if item is not None:
                    item.setBackground(_MAPPING_DEFAULT_BG)
                    item.setForeground(_MAPPING_DEFAULT_FG)

        colored_columns: dict[int, QColor] = {}

        for field in self._fields:
            selected = self._field_to_selected_value.get(field.key, "")
            if selected == "":
                continue

            color = self._field_color(field.key)

            if field.key.endswith("_prefix"):
                if selected == "":
                    indices = [i for i, col in enumerate(columns) if self._is_int_column_name(col)]
                else:
                    indices = [i for i, col in enumerate(columns) if col.startswith(selected)]
            else:
                indices = [i for i, col in enumerate(columns) if col == selected]

            for idx in indices:
                colored_columns[idx] = color

        for col_idx, color in colored_columns.items():
            for row_idx in range(rows):
                item = self._model.item(row_idx, col_idx)
                if item is not None:
                    item.setBackground(color)
                    item.setForeground(_MAPPING_HIGHLIGHT_FG)

    def _on_accept(self) -> None:
        missing: list[str] = []

        for field in self._fields:
            value = (
                self._combos[field.key].currentText()
                if field.key in self._combos
                else self._line_edits[field.key].text()
            )
            if field.required and not value and field.key != "assignment_prefix":
                missing.append(field.label)

        if missing:
            QMessageBox.warning(
                self,
                "Neúplné mapování",
                "Prosím doplňte povinná pole:\n" + ", ".join(missing),
            )
            return

        result: dict[str, str] = {}
        for field in self._fields:
            if field.key in self._combos:
                result[field.key] = self._combos[field.key].currentText()
            else:
                result[field.key] = self._line_edits[field.key].text()

        self.result_mapping = result
        self.accept()