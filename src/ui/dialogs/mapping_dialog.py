import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QTableView,
    QVBoxLayout,
)

LOGICAL_FIELDS = {
    "competitions": [
        ("id",               "ID soutěže",           True),
        ("title",            "Název",                True),
        ("discipline",       "Disciplína",           True),
        ("age",              "Věková kategorie",     True),
        ("rank",             "Třída",                True),
        ("competitor_count", "Počet závodníků",      True),
        ("round_count",      "Počet kol",            True),
    ],
    "competitors": [
        ("count",            "Počet závodníků páru", True),
        ("p1_name_surname",  "Jméno závodníka 1",    True),
        ("p2_name_surname",  "Jméno závodníka 2",    False),
        ("assignment_prefix","Prefix přiřazení",     True),
    ],
    "jury": [
        ("id",               "ID porotce",           True),
        ("name",             "Jméno",                True),
        ("surname",          "Příjmení",             True),
        ("assignment_prefix","Prefix přiřazení",     True),
    ],
    "schedule": [
        ("competition_id",   "ID soutěže",           True),
        ("start_time",       "Čas začátku",          True),
        ("duration",         "Délka (minuty)",       True),
        ("round_type",       "Typ kola",             True),
        ("end_time",         "Čas konce",            False),
    ],
}

_COL_HIGHLIGHT = QColor("green")
_ROW_HIGHLIGHT = QColor("green")
_DEFAULT_BG    = QColor("dark-gray")


class MappingDialog(QDialog):
    """Dialog for mapping DataFrame columns to logical fields."""

    def __init__(self, table_key: str, df: pd.DataFrame,
                 existing_mapping: dict = None, existing_rows: list = None,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mapování sloupců")
        self.resize(900, 600)

        self._table_key = table_key
        self._df = df
        self._fields = LOGICAL_FIELDS.get(table_key, [])
        self._selected_cols: set[int] = set()
        self._selected_rows: set[int] = set()
        self.result_mapping: dict = {}
        self.result_rows = None

        layout = QVBoxLayout(self)

        # Instruction label
        instruction = QLabel(
            "Klikněte na záhlaví sloupce pro výběr sloupce, na číslo řádku pro výběr řádku.\n"
            "Shift+klik = rozsah, Ctrl+klik = vícenásobný výběr."
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
                self._model.setItem(r, c, item)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.horizontalHeader().sectionClicked.connect(self._toggle_column)
        self._table.verticalHeader().sectionClicked.connect(self._toggle_row)
        layout.addWidget(self._table)

        # Pre-select rows from existing_rows
        if existing_rows:
            for r in existing_rows:
                self._selected_rows.add(r)
            self._refresh_highlights()
        self._refresh_highlights()

        # Mapping form
        group = QGroupBox("Mapování sloupců")
        form = QFormLayout(group)
        self._combos: dict[str, QComboBox] = {}
        columns = list(df.columns)

        for field_key, label, required in self._fields:
            combo = QComboBox()
            if not required:
                combo.addItem("")
            combo.addItems(columns)
            if existing_mapping and field_key in existing_mapping:
                idx = combo.findText(existing_mapping[field_key])
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            self._combos[field_key] = combo
            display_label = f"{label} *" if required else label
            form.addRow(display_label, combo)

        layout.addWidget(group)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Potvrdit")
        buttons.button(QDialogButtonBox.Cancel).setText("Zrušit")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    # Column / row selection helpers
    # ------------------------------------------------------------------

    def _toggle_column(self, col: int) -> None:
        if col in self._selected_cols:
            self._selected_cols.discard(col)
        else:
            self._selected_cols.add(col)
        self._refresh_highlights()

    def _toggle_row(self, row: int) -> None:
        if row in self._selected_rows:
            self._selected_rows.discard(row)
        else:
            self._selected_rows.add(row)
        self._refresh_highlights()

    def _refresh_highlights(self) -> None:
        rows = self._model.rowCount()
        cols = self._model.columnCount()
        for r in range(rows):
            for c in range(cols):
                item = self._model.item(r, c)
                if item is None:
                    continue
                if c in self._selected_cols:
                    item.setBackground(_COL_HIGHLIGHT)
                elif r in self._selected_rows:
                    item.setBackground(_ROW_HIGHLIGHT)
                else:
                    item.setBackground(_DEFAULT_BG)

    # ------------------------------------------------------------------
    # Accept / validate
    # ------------------------------------------------------------------

    def _on_accept(self) -> None:
        missing_labels = []
        for field_key, label, required in self._fields:
            if required and not self._combos[field_key].currentText():
                missing_labels.append(label)

        if missing_labels:
            QMessageBox.warning(
                self,
                "Neúplné mapování",
                f"Prosím vyberte sloupce pro povinná pole:\n{', '.join(missing_labels)}",
            )
            return

        self.result_mapping = {
            field_key: self._combos[field_key].currentText()
            for field_key, _, _ in self._fields
        }
        self.result_rows = sorted(self._selected_rows) if self._selected_rows else None
        self.accept()
