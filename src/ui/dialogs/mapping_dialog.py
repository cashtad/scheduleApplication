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

from core import TABLE_CONFIGS
from ..constants import (
    MAPPING_DEFAULT_BG,
    MAPPING_DEFAULT_FG,
    MAPPING_HIGHLIGHT_COLORS,
    MAPPING_HIGHLIGHT_FG,
)

_PREFIX_RE = re.compile(r"^(.*?)(\d+)$")


class MappingDialog(QDialog):
    """Dialog for mapping DataFrame columns to logical fields."""

    def __init__(self, table_key: str, df: pd.DataFrame,
                 existing_mapping: Optional[dict] = None,
                 existing_rows: Optional[list] = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mapování sloupců")
        self.resize(900, 600)

        self._table_key = table_key
        self._df = df
        cfg = TABLE_CONFIGS.get(table_key)
        self._fields: list[tuple[str, str, bool]] = (
            [(f.key, f.label, f.required) for f in cfg.fields] if cfg else []
        )
        self._combos: dict[str, QComboBox] = {}
        self._line_edits: dict[str, QLineEdit] = {}
        self._prefix_hint_labels: dict[str, QLabel] = {}
        self._field_col_map: dict[str, str] = {}
        self.result_mapping: dict = {}
        self.result_rows = None

        layout = QVBoxLayout(self)

        # Instruction label
        instruction = QLabel(
            "Vyberte sloupce pro každé pole pomocí rozevíracích seznamů níže.\n"
            "Vybraný sloupec se automaticky zvýrazní v tabulce."
        )
        layout.addWidget(instruction)

        # Table view
        self._model = QStandardItemModel(len(df), len(df.columns))
        self._model.setHorizontalHeaderLabels(list(df.columns))
        self._model.setVerticalHeaderLabels([str(i + 1) for i in range(len(df))])

        for r, row in enumerate(df.itertuples(index=False)):
            for c, val in enumerate(row):
                item = QStandardItem(str(val))
                item.setFlags(Qt.ItemIsEnabled)
                # Explicitly set default colors so the table is always readable
                item.setBackground(MAPPING_DEFAULT_BG)
                item.setForeground(MAPPING_DEFAULT_FG)
                self._model.setItem(r, c, item)

        self._table = QTableView()
        self._table.setModel(self._model)
        layout.addWidget(self._table)

        # Mapping form
        group = QGroupBox("Mapování sloupců")
        form = QFormLayout(group)
        columns = list(df.columns)

        for field_key, label, required in self._fields:
            display_label = f"{label} *" if required else label
            existing_val = existing_mapping.get(field_key, "") if existing_mapping else ""
            color = self._field_color(field_key)

            if field_key.endswith("_prefix"):
                inner = self._build_prefix_widget(field_key, existing_val)
                widget = self._wrap_with_swatch(color, inner)
                form.addRow(display_label, widget)
            else:
                combo = QComboBox()
                if not required:
                    combo.addItem("")
                combo.addItems(columns)
                if existing_val:
                    idx = combo.findText(existing_val)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                combo.currentTextChanged.connect(
                    lambda text, fk=field_key: self._on_combo_changed(fk, text)
                )
                self._combos[field_key] = combo
                form.addRow(display_label, self._wrap_with_swatch(color, combo))

        layout.addWidget(group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Potvrdit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Populate _field_col_map from existing_mapping and do initial highlights
        if existing_mapping:
            for field_key, _, _ in self._fields:
                if field_key in existing_mapping:
                    self._field_col_map[field_key] = existing_mapping[field_key]
        for field_key, _, _ in self._fields:
            if field_key.endswith("_prefix"):
                prefix_text = self._field_col_map.get(field_key, "")
                self._update_prefix_hint(field_key, prefix_text)
        self._refresh_highlights()

    # ------------------------------------------------------------------
    # Prefix widget builder
    # ------------------------------------------------------------------

    def _build_prefix_widget(self, field_key: str, existing_val: str) -> QWidget:
        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)

        line_edit = QLineEdit()
        line_edit.setText(existing_val)
        line_edit.textChanged.connect(
            lambda text, fk=field_key: self._on_prefix_changed(fk, text)
        )
        self._line_edits[field_key] = line_edit
        hbox.addWidget(line_edit)

        btn = QPushButton("Najít automaticky")
        btn.clicked.connect(lambda checked=False, fk=field_key: self._auto_detect_prefix(fk))
        hbox.addWidget(btn)

        hint_label = QLabel("→ 0 sloupců")
        self._prefix_hint_labels[field_key] = hint_label
        hbox.addWidget(hint_label)

        return container

    # ------------------------------------------------------------------
    # Per-field color helpers
    # ------------------------------------------------------------------

    def _field_color(self, field_key: str) -> QColor:
        """Return the stable highlight color for *field_key* based on its position in self._fields."""
        for idx, (fk, _, _) in enumerate(self._fields):
            if fk == field_key:
                return MAPPING_HIGHLIGHT_COLORS[idx % len(MAPPING_HIGHLIGHT_COLORS)]
        return MAPPING_HIGHLIGHT_COLORS[0]

    @staticmethod
    def _make_color_swatch(color: QColor) -> QLabel:
        """Create a 12×12 colored square label used as a visual field indicator."""
        swatch = QLabel()
        swatch.setFixedSize(12, 12)
        swatch.setStyleSheet(
            f"background-color: {color.name()}; border: 1px solid #888888; border-radius: 2px;"
        )
        return swatch

    def _wrap_with_swatch(self, color: QColor, widget: QWidget) -> QWidget:
        """Return a new widget containing a colored swatch followed by *widget*."""
        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)
        hbox.addWidget(self._make_color_swatch(color))
        hbox.addWidget(widget, stretch=1)
        return container

    # ------------------------------------------------------------------
    # Auto-detect prefix
    # ------------------------------------------------------------------

    def _auto_detect_prefix(self, field_key: str) -> None:
        cols = list(self._df.columns)
        groups: dict[str, list[int]] = {}
        for col in cols:
            m = _PREFIX_RE.match(str(col))
            if m:
                prefix, num_str = m.group(1), m.group(2)
                groups.setdefault(prefix, []).append(int(num_str))

        candidates: list[tuple[str, int]] = []
        for prefix, numbers in groups.items():
            sorted_nums = sorted(numbers)
            n = len(sorted_nums)
            if n >= 2 and sorted_nums == list(range(1, n + 1)):
                candidates.append((prefix, n))

        if len(candidates) == 0:
            QMessageBox.information(
                self,
                "Automatická detekce",
                "Nepodařilo se automaticky detekovat prefix. Zadejte jej ručně.",
            )
            return

        if len(candidates) == 1:
            self._line_edits[field_key].setText(candidates[0][0])
            return

        descriptions = []
        for prefix, count in candidates:
            if prefix == "":
                descriptions.append(f"číselné sloupce bez prefixu  ({count} sloupců)")
            else:
                descriptions.append(f"{prefix}  ({count} sloupců)")

        item, ok = QInputDialog.getItem(
            self,
            "Vyberte prefix",
            "Nalezeno více kandidátů. Vyberte prefix:",
            descriptions,
            0,
            False,
        )
        if ok and item:
            idx = descriptions.index(item)
            self._line_edits[field_key].setText(candidates[idx][0])

    # ------------------------------------------------------------------
    # Combo / lineedit change handlers
    # ------------------------------------------------------------------

    def _on_combo_changed(self, field_key: str, col_name: str) -> None:
        self._field_col_map[field_key] = col_name
        self._refresh_highlights()

    def _on_prefix_changed(self, field_key: str, prefix_text: str) -> None:
        self._field_col_map[field_key] = prefix_text
        self._refresh_highlights()
        self._update_prefix_hint(field_key, prefix_text)

    # ------------------------------------------------------------------
    # Prefix hint label
    # ------------------------------------------------------------------

    def _update_prefix_hint(self, field_key: str, prefix_text: str) -> None:
        label = self._prefix_hint_labels.get(field_key)
        if label is None:
            return
        if prefix_text == "":
            matching = [c for c in self._df.columns if self._is_pure_int(str(c))]
        else:
            matching = [c for c in self._df.columns if str(c).startswith(prefix_text)]
        label.setText(f"→ {len(matching)} sloupců")

    @staticmethod
    def _is_pure_int(s: str) -> bool:
        try:
            int(s)
            return True
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    # Highlight logic
    # ------------------------------------------------------------------

    def _refresh_highlights(self) -> None:
        rows = self._model.rowCount()
        cols = self._model.columnCount()
        df_cols = list(self._df.columns)

        # Reset all cells to explicit white background + black text
        for r in range(rows):
            for c in range(cols):
                item = self._model.item(r, c)
                if item is not None:
                    item.setBackground(MAPPING_DEFAULT_BG)
                    item.setForeground(MAPPING_DEFAULT_FG)

        # Build col_index -> color mapping
        col_colors: dict[int, QColor] = {}
        for field_key, _, _ in self._fields:
            color = self._field_color(field_key)
            if field_key not in self._field_col_map:
                continue
            val = self._field_col_map[field_key]

            if field_key.endswith("_prefix"):
                if val == "":
                    indices = [i for i, name in enumerate(df_cols) if self._is_pure_int(str(name))]
                else:
                    indices = [i for i, name in enumerate(df_cols) if str(name).startswith(val)]
            else:
                indices = [i for i, name in enumerate(df_cols) if name == val]

            for i in indices:
                col_colors[i] = color

        # Paint matched columns with highlight color + dark text
        for c, color in col_colors.items():
            for r in range(rows):
                item = self._model.item(r, c)
                if item is not None:
                    item.setBackground(color)
                    item.setForeground(MAPPING_HIGHLIGHT_FG)

    # ------------------------------------------------------------------
    # Accept / validate
    # ------------------------------------------------------------------

    def _on_accept(self) -> None:
        missing_labels = []
        for field_key, label, required in self._fields:
            if required:
                if field_key in self._combos:
                    val = self._combos[field_key].currentText()
                else:
                    val = self._line_edits[field_key].text()
                if not val and field_key != "assignment_prefix":
                    missing_labels.append(label)

        if missing_labels:
            QMessageBox.warning(
                self,
                "Neúplné mapování",
                f"Prosím vyberte sloupce pro povinná pole:\n{', '.join(missing_labels)}",
            )
            return

        self.result_mapping = {}
        for field_key, _, _ in self._fields:
            if field_key in self._combos:
                self.result_mapping[field_key] = self._combos[field_key].currentText()
            else:
                self.result_mapping[field_key] = self._line_edits[field_key].text()
        self.accept()
