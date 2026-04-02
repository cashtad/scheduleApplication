from __future__ import annotations

from typing import Callable

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

from src.application.contracts import TABLE_MAPPING_SCHEMAS
from src.presentation.qt.controllers import UiController
from src.presentation.qt.dialogs.mapping_dialog import MappingDialog
from src.session import TableStatus

_DOT_STYLE = "border-radius: 8px; width: 16px; height: 16px; background-color: {color};"

_TABLE_LABELS = {
    "competitions": "Soutěže",
    "competitors": "Účastníci",
    "jury": "Porotci",
    "schedule": "Rozvrh",
}

_STATUS_UI = {
    TableStatus.EMPTY: ("Nevybráno", "#9E9E9E"),
    TableStatus.FILE_SELECTED: ("Soubor vybrán", "#29B6F6"),
    TableStatus.SHEET_SELECTED: ("List vybrán", "#FFA726"),
    TableStatus.MAPPED: ("Namapováno", "#FFCA28"),
    TableStatus.READY: ("Připraveno", "#66BB6A"),
    TableStatus.BROKEN_PATH: ("Neplatná cesta", "#EF5350"),
    TableStatus.BROKEN_SHEET: ("Neplatný list", "#EF5350"),
    TableStatus.MAPPING_STALE: ("Mapování zastaralé", "#AB47BC"),
}


class TableLoadPanel(QWidget):
    status_changed = Signal()

    def __init__(
        self,
        table_key: str,
        controller: UiController,
        on_schedule_preview_changed: Callable[[object], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._table_key = table_key
        self._controller = controller
        self._on_schedule_preview_changed = on_schedule_preview_changed

        root = QVBoxLayout(self)

        title = QLabel(_TABLE_LABELS.get(table_key, table_key))
        title.setStyleSheet("font-weight: 600;")
        root.addWidget(title)

        status_row = QHBoxLayout()
        self._dot = QLabel()
        self._dot.setFixedSize(16, 16)
        self._status_label = QLabel()
        status_row.addWidget(self._dot)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        root.addLayout(status_row)

        self._action_btn = QPushButton()
        self._action_btn.clicked.connect(self._on_action_clicked)
        root.addWidget(self._action_btn)

        self.refresh()

    def refresh(self) -> None:
        status = self._controller.get_table_status(self._table_key)
        text, color = _STATUS_UI.get(status, (status.value, "#9E9E9E"))
        self._dot.setStyleSheet(_DOT_STYLE.format(color=color))
        self._status_label.setText(text)
        self._action_btn.setText(
            "Změnit" if status in {TableStatus.MAPPED, TableStatus.READY} else "Načíst"
        )
        self.status_changed.emit()

    def _on_action_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Vyberte soubor tabulky", "", "Tabulky (*.xlsx *.xls)"
        )
        if not file_path:
            return

        self._controller.set_file(self._table_key, file_path)

        try:
            sheet_names = self._controller.excel_reader.get_sheet_names(file_path)
        except Exception as exc:
            QMessageBox.critical(
                self, "Chyba načítání", f"Nelze otevřít soubor:\n{exc}"
            )
            self.refresh()
            return

        if not sheet_names:
            QMessageBox.critical(
                self, "Chyba načítání", "Soubor neobsahuje žádné listy."
            )
            self.refresh()
            return

        if len(sheet_names) == 1:
            sheet_name = sheet_names[0]
        else:
            selected, ok = QInputDialog.getItem(
                self, "Výběr listu", "Vyberte list tabulky:", sheet_names, 0, False
            )
            if not ok:
                self.refresh()
                return
            sheet_name = selected

        self._controller.set_sheet(self._table_key, sheet_name)

        try:
            df = self._controller.excel_reader.read(file_path, sheet_name)
        except Exception as exc:
            QMessageBox.critical(self, "Chyba načítání", f"Nelze načíst list:\n{exc}")
            self.refresh()
            return

        existing_mapping = self._controller.session.get_table(
            self._table_key
        ).column_mapping
        dlg = MappingDialog(
            table_key=self._table_key,
            df=df,
            existing_mapping=existing_mapping,
            parent=self,
        )
        if dlg.exec() != MappingDialog.Accepted:
            self.refresh()
            return

        mapping = dict(dlg.result_mapping)
        ok, error_text = self._validate_mapping_preflight(
            mapping, [str(c) for c in df.columns]
        )
        if not ok:
            QMessageBox.warning(self, "Neplatné mapování", error_text)
            self.refresh()
            return

        self._controller.set_mapping(
            table_key=self._table_key,
            column_mapping=mapping,
            current_columns=[str(c) for c in df.columns],
        )
        self._controller.mark_ready(self._table_key)

        if (
            self._table_key == "schedule"
            and self._on_schedule_preview_changed is not None
        ):
            self._on_schedule_preview_changed(df)

        self.refresh()

    def _validate_mapping_preflight(
        self, mapping: dict[str, str], current_columns: list[str]
    ) -> tuple[bool, str]:
        schema = TABLE_MAPPING_SCHEMAS[self._table_key]
        existing_columns = set(current_columns)

        for field in schema.fields:
            val = (mapping.get(field.key) or "").strip()
            if field.required and not val:
                return False, f"Povinné pole '{field.label}' není vyplněno."

        for field in schema.fields:
            if field.virtual:
                continue
            val = (mapping.get(field.key) or "").strip()
            if val and val not in existing_columns:
                return (
                    False,
                    f"Vybraný sloupec '{val}' pro pole '{field.label}' neexistuje v tabulce.",
                )

        if self._table_key in {"competitors", "jury"}:
            prefix = (mapping.get("assignment_prefix") or "").strip()
            if prefix:
                matched = [c for c in current_columns if c.startswith(prefix)]
                if not matched:
                    return False, f"Prefix '{prefix}' neodpovídá žádnému sloupci."
            else:
                numeric = [c for c in current_columns if c.strip().isdigit()]
                if not numeric:
                    return (
                        False,
                        "Pro prázdný prefix nebyly nalezeny číselné sloupce přiřazení.",
                    )

        if self._table_key == "jury":
            fullname = (mapping.get("fullname") or "").strip()
            name = (mapping.get("name") or "").strip()
            surname = (mapping.get("surname") or "").strip()
            if not fullname and not (name and surname):
                return (
                    False,
                    "Pro porotu je potřeba buď 'Celé jméno', nebo kombinace 'Jméno' + 'Příjmení'.",
                )

        return True, ""
