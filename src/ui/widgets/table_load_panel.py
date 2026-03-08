import pandas as pd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core import TableSession
from data import ExcelTableLoader, TemplateStore
from ..dialogs import MappingDialog

TABLE_NAMES = {
    "competitions": "Tabulka soutěží",
    "competitors": "Tabulka závodníků",
    "jury": "Tabulka porotců",
    "schedule": "Tabulka harmonogramu",
}

STATUS_CONFIG = {
    "not_loaded": ("Nevybráno", "#9E9E9E"),
    "needs_mapping": ("Vyžaduje výběr sloupců", "#FF9800"),
    "ready": ("Připraveno", "#4CAF50"),
}

_DOT_STYLE = (
    "border-radius: 8px; width: 16px; height: 16px; background-color: {color};"
)


class TableLoadPanel(QWidget):
    """Widget for loading and mapping a single table file."""

    status_changed = Signal()

    def __init__(self, table_key: str, session, parent=None):
        super().__init__(parent)
        self._table_key = table_key
        self._session = session
        self._status = "not_loaded"

        # Pending state (file loaded but not yet mapped)
        self.pending_df: pd.DataFrame | None = None
        self.pending_path: str | None = None
        self.pending_sheet: str | None = None

        layout = QVBoxLayout(self)

        # Table name label
        name_label = QLabel(TABLE_NAMES.get(table_key, table_key))
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)

        # Status row
        status_row = QHBoxLayout()
        self._dot = QLabel()
        self._dot.setFixedSize(16, 16)
        self._status_label = QLabel()
        status_row.addWidget(self._dot)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        layout.addLayout(status_row)

        # Load button
        self._load_btn = QPushButton("Načíst")
        self._load_btn.clicked.connect(self._on_load_clicked)
        layout.addWidget(self._load_btn)

        self.set_status("not_loaded")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_status(self, status: str) -> None:
        self._status = status
        text, color = STATUS_CONFIG[status]
        self._dot.setStyleSheet(_DOT_STYLE.format(color=color))
        self._status_label.setText(text)
        self._load_btn.setText("Změnit" if status == "ready" else "Načíst")

    # ------------------------------------------------------------------
    # Load button flow
    # ------------------------------------------------------------------

    def _on_load_clicked(self) -> None:
        if self._status == "needs_mapping" and self.pending_df is not None:
            # User wants to map the already-loaded file
            self._open_mapping_dialog(self.pending_df, self.pending_path, self.pending_sheet)
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte soubor tabulky",
            "",
            "Tabulky (*.xlsx *.xls)",
        )
        if not file_path:
            return

        # Determine sheet
        sheet_name = None
        try:
            sheet_names = pd.ExcelFile(file_path).sheet_names
        except Exception as exc:
            QMessageBox.critical(self, "Chyba načítání", f"Nelze otevřít soubor:\n{exc}")
            return

        if len(sheet_names) > 1:
            chosen, ok = QInputDialog.getItem(
                self,
                "Výběr listu",
                "Vyberte list tabulky:",
                sheet_names,
                0,
                False,
            )
            if not ok:
                return
            sheet_name = chosen
        elif len(sheet_names) == 1:
            sheet_name = sheet_names[0]
        else:
            QMessageBox.critical(self, "Chyba načítání", "Soubor neobsahuje žádné listy.")
            return

        # Load DataFrame
        try:
            loader = ExcelTableLoader(path=file_path, sheet=sheet_name)
            raw_df = loader.load()
        except Exception as exc:
            QMessageBox.critical(self, "Chyba načítání", f"Nelze načíst tabulku:\n{exc}")
            return

        # Try auto-apply template
        auto_mapping = TemplateStore().try_auto_apply(self._table_key, list(raw_df.columns))
        if auto_mapping is not None:
            answer = QMessageBox.question(
                self,
                "Uložená šablona",
                "Nalezena uložená šablona pro tuto tabulku. Použít automaticky?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if answer == QMessageBox.Yes:
                self._apply_mapping(raw_df, file_path, sheet_name, auto_mapping, None)
                return

        self._open_mapping_dialog(raw_df, file_path, sheet_name)

    def _open_mapping_dialog(self, raw_df: pd.DataFrame, file_path: str, sheet_name) -> None:
        existing_ts = self._session.tables.get(self._table_key)
        existing_mapping = existing_ts.column_mapping if existing_ts else None
        existing_rows = existing_ts.selected_rows if existing_ts else None

        dlg = MappingDialog(
            self._table_key,
            raw_df,
            existing_mapping=existing_mapping,
            existing_rows=existing_rows,
            parent=self,
        )
        if dlg.exec() == MappingDialog.Accepted:
            mapping = dlg.result_mapping
            selected_rows = dlg.result_rows
            TemplateStore().save_mapping(self._table_key, mapping, list(raw_df.columns))
            self._apply_mapping(raw_df, file_path, sheet_name, mapping, selected_rows)
        # else: keep previous status unchanged

    def _apply_mapping(
            self,
            raw_df: pd.DataFrame,
            file_path: str,
            sheet_name,
            mapping: dict,
            selected_rows,
    ) -> None:
        self._session.tables[self._table_key] = TableSession(
            table_key=self._table_key,
            file_path=file_path,
            sheet_name=sheet_name,
            raw_df=raw_df,
            column_mapping=mapping,
            selected_rows=selected_rows,
        )
        # Clear pending state
        self.pending_df = None
        self.pending_path = None
        self.pending_sheet = None
        self.set_status("ready")
        self.status_changed.emit()
