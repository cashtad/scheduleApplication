from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pandas import DataFrame
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


@dataclass(slots=True)
class TableLoadContext:
    file_path: str
    sheet_name: str
    df: DataFrame
    current_columns: list[str]
    previous_mapping: dict[str, str]
    reusable_mapping: dict[str, str] | None


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
        context = self._build_load_context()
        if context is None:
            return

        self._commit_file_and_sheet(context)

        if self._try_auto_apply_reusable_mapping(context):
            self._finalize_success(context.df)
            return

        if self._open_mapping_dialog_and_apply(context):
            self._finalize_success(context.df)
            return

        self.refresh()

    def _build_load_context(self) -> TableLoadContext | None:
        previous_mapping = dict(
            self._controller.session.get_table(self._table_key).column_mapping
        )

        file_path = self._choose_file_path()
        if file_path is None:
            return None

        sheet_name = self._choose_sheet_name(file_path)
        if sheet_name is None:
            return None

        df = self._read_dataframe(file_path, sheet_name)
        if df is None:
            return None

        current_columns = [str(c) for c in df.columns]
        reusable_mapping = self._controller.get_applicable_mapping_for_columns(
            table_key=self._table_key,
            mapping=previous_mapping,
            current_columns=current_columns,
        )

        return TableLoadContext(
            file_path=file_path,
            sheet_name=sheet_name,
            df=df,
            current_columns=current_columns,
            previous_mapping=previous_mapping,
            reusable_mapping=reusable_mapping,
        )

    def _choose_file_path(self) -> str | None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vyberte soubor tabulky",
            "",
            "Tabulky (*.xlsx *.xls)",
        )
        return file_path or None

    def _choose_sheet_name(self, file_path: str) -> str | None:
        try:
            sheet_names = self._controller.get_sheet_names(file_path)
        except Exception as exc:
            QMessageBox.critical(
                self, "Chyba načítání", f"Nelze otevřít soubor:\n{exc}"
            )
            self.refresh()
            return None

        if not sheet_names:
            QMessageBox.critical(
                self, "Chyba načítání", "Soubor neobsahuje žádné listy."
            )
            self.refresh()
            return None

        if len(sheet_names) == 1:
            return sheet_names[0]

        selected, ok = QInputDialog.getItem(
            self,
            "Výběr listu",
            "Vyberte list tabulky:",
            sheet_names,
            0,
            False,
        )
        return selected if ok else None

    def _read_dataframe(self, file_path: str, sheet_name: str) -> DataFrame | None:
        try:
            return self._controller.read(file_path, sheet_name)
        except Exception as exc:
            QMessageBox.critical(self, "Chyba načítání", f"Nelze načíst list:\n{exc}")
            self.refresh()
            return None

    def _commit_file_and_sheet(self, context: TableLoadContext) -> None:
        self._controller.set_file(self._table_key, context.file_path)
        self._controller.set_sheet(self._table_key, context.sheet_name)

    def _try_auto_apply_reusable_mapping(self, context: TableLoadContext) -> bool:
        if not context.reusable_mapping:
            return False

        answer = QMessageBox.question(
            self,
            "Existující mapování",
            "Bylo nalezeno použitelné uložené mapování.\nPoužít ho automaticky?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer != QMessageBox.Yes:
            return False

        ok, message = self._controller.apply_mapping_and_mark_ready(
            table_key=self._table_key,
            mapping=context.reusable_mapping,
            current_columns=context.current_columns,
        )
        if not ok:
            QMessageBox.warning(self, "Neplatné mapování", message)
            return False

        return True

    def _open_mapping_dialog_and_apply(self, context: TableLoadContext) -> bool:
        dialog = MappingDialog(
            table_key=self._table_key,
            df=context.df,
            existing_mapping=context.reusable_mapping or context.previous_mapping,
            parent=self,
        )
        if dialog.exec() != MappingDialog.Accepted:
            return False

        ok, message = self._controller.apply_mapping_and_mark_ready(
            table_key=self._table_key,
            mapping=dict(dialog.result_mapping),
            current_columns=context.current_columns,
        )
        if not ok:
            QMessageBox.warning(self, "Neplatné mapování", message)
            return False

        return True

    def _finalize_success(self, df: DataFrame) -> None:
        if (
            self._table_key == "schedule"
            and self._on_schedule_preview_changed is not None
        ):
            self._on_schedule_preview_changed(df)
        self.refresh()
