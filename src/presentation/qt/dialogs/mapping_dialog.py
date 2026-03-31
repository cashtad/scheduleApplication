from __future__ import annotations

import re
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

from src.application.contracts import TABLE_MAPPING_SCHEMAS, MappingField

_MAPPING_HIGHLIGHT_COLORS = [
    QColor("#BBDEFB"),
    QColor("#C8E6C9"),
    QColor("#FFE0B2"),
    QColor("#F8BBD9"),
    QColor("#E1BEE7"),
    QColor("#B2EBF2"),
    QColor("#FFF9C4"),
]
_MAPPING_DEFAULT_BG = QColor("#FFFFFF")
_MAPPING_DEFAULT_FG = QColor("#000000")
_MAPPING_HIGHLIGHT_FG = QColor("#000000")

_PREFIX_RE = re.compile(r"^(.*?)(\d+)$")


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
        self.resize(980, 640)

        self._table_key = table_key
        self._df = df
        schema = TABLE_MAPPING_SCHEMAS.get(table_key)
        self._fields: list[MappingField] = list(schema.fields) if schema else []

        self._combos: dict[str, QComboBox] = {}
        self._line_edits: dict[str, QLineEdit] = {}
        self._prefix_hint_labels: dict[str, QLabel] = {}
        self._selected_values: dict[str, str] = {}
        self.result_mapping: dict[str, str] = {}

        root = QVBoxLayout(self)

        hint = QLabel(
            "Vyberte sloupce pro jednotlivá pole. "
            "Vybrané sloupce se automaticky zvýrazní."
        )
        root.addWidget(hint)

        self._model = QStandardItemModel(len(df), len(df.columns))
        self._model.setHorizontalHeaderLabels([str(c) for c in df.columns])
        self._model.setVerticalHeaderLabels([str(i + 1) for i in range(len(df))])

        for r, row in enumerate(df.itertuples(index=False)):
            for c, val in enumerate(row):
                item = QStandardItem(str(val))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setBackground(_MAPPING_DEFAULT_BG)
                item.setForeground(_MAPPING_DEFAULT_FG)
                self._model.setItem(r, c, item)

        table = QTableView()
        table.setModel(self._model)
        table.resizeColumnsToContents()
        root.addWidget(table)

        group = QGroupBox("Mapování polí")
        form = QFormLayout(group)
        columns = [str(c) for c in df.columns]

        for field in self._fields:
            existing_val = (existing_mapping or {}).get(field.key, "")
            display_label = f"{field.label} *" if field.required else field.label
            color = self._field_color(field.key)

            if field.key.endswith("_prefix"):
                editor = self._build_prefix_editor(field.key, existing_val)
                form.addRow(display_label, self._wrap_with_swatch(color, editor))
            else:
                combo = QComboBox()
                if not field.required:
                    combo.addItem("")
                combo.addItems(columns)
                if existing_val:
                    idx = combo.findText(existing_val)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                combo.currentTextChanged.connect(
                    lambda text, fk=field.key: self._on_combo_changed(fk, text)
                )
                self._combos[field.key] = combo
                form.addRow(display_label, self._wrap_with_swatch(color, combo))

        root.addWidget(group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Potvrdit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        if existing_mapping:
            for k, v in existing_mapping.items():
                self._selected_values[k] = v

        for field in self._fields:
            if field.key.endswith("_prefix"):
                self._update_prefix_hint(field.key, self._selected_values.get(field.key, ""))

        self._refresh_highlights()

    def _build_prefix_editor(self, field_key: str, existing_value: str) -> QWidget:
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)

        edit = QLineEdit(existing_value)
        edit.textChanged.connect(lambda text, fk=field_key: self._on_prefix_changed(fk, text))
        self._line_edits[field_key] = edit
        row.addWidget(edit)

        btn = QPushButton("Najít automaticky")
        btn.clicked.connect(lambda _=False, fk=field_key: self._auto_detect_prefix(fk))
        row.addWidget(btn)

        hint = QLabel("→ 0 sloupců")
        self._prefix_hint_labels[field_key] = hint
        row.addWidget(hint)

        return box

    def _field_color(self, field_key: str) -> QColor:
        for idx, field in enumerate(self._fields):
            if field.key == field_key:
                return _MAPPING_HIGHLIGHT_COLORS[idx % len(_MAPPING_HIGHLIGHT_COLORS)]
        return _MAPPING_HIGHLIGHT_COLORS[0]

    @staticmethod
    def _wrap_with_swatch(color: QColor, inner: QWidget) -> QWidget:
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        swatch = QLabel()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #888; border-radius: 2px;"
        )

        row.addWidget(swatch)
        row.addWidget(inner, stretch=1)
        return box

    def _on_combo_changed(self, field_key: str, value: str) -> None:
        self._selected_values[field_key] = value
        self._refresh_highlights()

    def _on_prefix_changed(self, field_key: str, value: str) -> None:
        self._selected_values[field_key] = value
        self._update_prefix_hint(field_key, value)
        self._refresh_highlights()

    def _auto_detect_prefix(self, field_key: str) -> None:
        groups: dict[str, list[int]] = {}
        for col in [str(c) for c in self._df.columns]:
            m = _PREFIX_RE.match(col)
            if not m:
                continue
            prefix, num = m.group(1), int(m.group(2))
            groups.setdefault(prefix, []).append(num)

        candidates: list[tuple[str, int]] = []
        for prefix, nums in groups.items():
            nums = sorted(nums)
            if len(nums) >= 2 and nums == list(range(1, len(nums) + 1)):
                candidates.append((prefix, len(nums)))

        if not candidates:
            QMessageBox.information(self, "Automatická detekce", "Prefix se nepodařilo detekovat.")
            return

        if len(candidates) == 1:
            self._line_edits[field_key].setText(candidates[0][0])
            return

        labels = [f"{p or 'bez prefixu'} ({n} sloupců)" for p, n in candidates]
        selected, ok = QInputDialog.getItem(
            self, "Vyberte prefix", "Nalezeno více kandidátů. Vyberte prefix:", labels, 0, False
        )
        if ok and selected:
            idx = labels.index(selected)
            self._line_edits[field_key].setText(candidates[idx][0])

    def _update_prefix_hint(self, field_key: str, prefix: str) -> None:
        label = self._prefix_hint_labels.get(field_key)
        if label is None:
            return

        cols = [str(c) for c in self._df.columns]
        if prefix == "":
            matched = [c for c in cols if c.strip().isdigit()]
        else:
            matched = [c for c in cols if c.startswith(prefix)]

        label.setText(f"→ {len(matched)} sloupců")

    def _refresh_highlights(self) -> None:
        rows = self._model.rowCount()
        cols = self._model.columnCount()
        df_cols = [str(c) for c in self._df.columns]

        for r in range(rows):
            for c in range(cols):
                item = self._model.item(r, c)
                if item:
                    item.setBackground(_MAPPING_DEFAULT_BG)
                    item.setForeground(_MAPPING_DEFAULT_FG)

        col_colors: dict[int, QColor] = {}
        for field in self._fields:
            val = self._selected_values.get(field.key, "")
            if not val:
                continue
            color = self._field_color(field.key)

            if field.key.endswith("_prefix"):
                indices = [i for i, name in enumerate(df_cols) if name.startswith(val)]
            else:
                indices = [i for i, name in enumerate(df_cols) if name == val]

            for i in indices:
                col_colors[i] = color

        for c, color in col_colors.items():
            for r in range(rows):
                item = self._model.item(r, c)
                if item:
                    item.setBackground(color)
                    item.setForeground(_MAPPING_HIGHLIGHT_FG)

    def _on_accept(self) -> None:
        result: dict[str, str] = {}
        for field in self._fields:
            if field.key in self._combos:
                result[field.key] = self._combos[field.key].currentText()
            else:
                result[field.key] = self._line_edits[field.key].text()

        missing = self._validate_required_fields(result)
        if missing:
            QMessageBox.warning(
                self,
                "Neúplné mapování",
                "Prosím doplňte povinná pole:\n" + ", ".join(missing),
            )
            return

        self.result_mapping = result
        self.accept()

    def _validate_required_fields(self, mapping: dict[str, str]) -> list[str]:
        missing: list[str] = []

        for field in self._fields:
            value = (mapping.get(field.key) or "").strip()
            if field.required and not value:
                missing.append(field.label)

        if self._table_key == "jury":
            fullname = (mapping.get("fullname") or "").strip()
            name = (mapping.get("name") or "").strip()
            surname = (mapping.get("surname") or "").strip()

            if not fullname and not (name and surname):
                missing.append("Celé jméno nebo kombinace Jméno + Příjmení")

        return missing