from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from pandas import DataFrame
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.application.contracts import TableKey, get_table_spec
from src.presentation.qt.controllers import UiController
from src.presentation.qt.dialogs import MappingDialog
from src.session import TableStatus

_DOT_STYLE = "border-radius: 8px; width: 16px; height: 16px; background-color: {color};"

@dataclass(frozen=True, slots=True)
class PanelStatusUiState:
    status_text: str
    color: str
    status_tooltip: str
    edit_visible: bool
    edit_enabled: bool
    edit_text: str
    edit_tooltip: str
    select_text: str
    select_enabled: bool
    select_tooltip: str


_STATUS_UI = {
    TableStatus.EMPTY: PanelStatusUiState(
        status_text="Nevybráno",
        color="#9E9E9E",
        status_tooltip="Nejprve vyberte soubor a list.",
        edit_visible=False,
        edit_enabled=False,
        edit_text="Pracovat s vybraným listem",
        edit_tooltip="Nejprve vyberte soubor.",
        select_text="Načíst",
        select_enabled=True,
        select_tooltip="Vyberte Excel soubor.",
    ),
    TableStatus.FILE_SELECTED: PanelStatusUiState(
        status_text="Soubor vybrán",
        color="#29B6F6",
        status_tooltip="Soubor je vybrán, je potřeba zvolit list.",
        edit_visible=True,
        edit_enabled=True,
        edit_text="Vybrat list",
        edit_tooltip="Vyberte list v aktuálním souboru.",
        select_text="Vybrat jiný",
        select_enabled=True,
        select_tooltip="Zvolit jiný soubor.",
    ),
    TableStatus.SHEET_SELECTED: PanelStatusUiState(
        status_text="List vybrán",
        color="#FFA726",
        status_tooltip="List je vybrán, nastavte mapování sloupců.",
        edit_visible=True,
        edit_enabled=True,
        edit_text="Namapovat sloupce",
        edit_tooltip="Otevřít mapování pro vybraný list.",
        select_text="Vybrat jiný",
        select_enabled=True,
        select_tooltip="Zvolit jiný soubor.",
    ),
    TableStatus.MAPPED: PanelStatusUiState(
        status_text="Namapováno",
        color="#FFCA28",
        status_tooltip="Mapování je uloženo, tabulka čeká na validaci.",
        edit_visible=True,
        edit_enabled=True,
        edit_text="Upravit mapování",
        edit_tooltip="Upravit mapování vybraného listu.",
        select_text="Vybrat jiný",
        select_enabled=True,
        select_tooltip="Zvolit jiný soubor.",
    ),
    TableStatus.READY: PanelStatusUiState(
        status_text="Připraveno",
        color="#66BB6A",
        status_tooltip="Tabulka je připravena pro analýzu.",
        edit_visible=True,
        edit_enabled=True,
        edit_text="Upravit mapování",
        edit_tooltip="Upravit mapování vybraného listu.",
        select_text="Vybrat jiný",
        select_enabled=True,
        select_tooltip="Zvolit jiný soubor.",
    ),
    TableStatus.BROKEN_PATH: PanelStatusUiState(
        status_text="Neplatná cesta",
        color="#EF5350",
        status_tooltip="Soubor nebyl nalezen. Vyberte platný soubor.",
        edit_visible=False,
        edit_enabled=False,
        edit_text="Pracovat s vybraným listem",
        edit_tooltip="Soubor není dostupný.",
        select_text="Vybrat soubor",
        select_enabled=True,
        select_tooltip="Zvolte platný soubor.",
    ),
    TableStatus.BROKEN_SHEET: PanelStatusUiState(
        status_text="Neplatný list",
        color="#EF5350",
        status_tooltip="Původní list neexistuje, vyberte jiný.",
        edit_visible=True,
        edit_enabled=True,
        edit_text="Vybrat list",
        edit_tooltip="Vyberte jiný list v aktuálním souboru.",
        select_text="Vybrat jiný",
        select_enabled=True,
        select_tooltip="Zvolit jiný soubor.",
    ),
    TableStatus.MAPPING_STALE: PanelStatusUiState(
        status_text="Mapování zastaralé",
        color="#AB47BC",
        status_tooltip="Sloupce se změnily, upravte mapování.",
        edit_visible=True,
        edit_enabled=True,
        edit_text="Upravit mapování",
        edit_tooltip="Upravte mapování podle aktuálních sloupců.",
        select_text="Vybrat jiný",
        select_enabled=True,
        select_tooltip="Zvolit jiný soubor.",
    ),
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
        self._full_path = ""
        self._table_spec = get_table_spec(table_key)

        root = QVBoxLayout(self)

        title = QLabel(self._table_spec.label_cz)
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

        self._path_label = QLabel()
        self._path_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self._path_label.setMinimumWidth(50)
        root.addWidget(self._path_label)

        actions_row = QHBoxLayout()
        self._edit_selected_btn = QPushButton()
        self._edit_selected_btn.clicked.connect(self._on_edit_selected_clicked)
        actions_row.addWidget(self._edit_selected_btn)

        self._select_other_btn = QPushButton()
        self._select_other_btn.clicked.connect(self._on_select_other_clicked)
        actions_row.addWidget(self._select_other_btn)
        root.addLayout(actions_row)

        self.refresh()

    def refresh(self) -> None:
        state = self._controller.get_table_state(self._table_key)
        status = state.status
        ui = _STATUS_UI.get(
            status,
            PanelStatusUiState(
                status_text=status.value,
                color="#9E9E9E",
                status_tooltip="",
                edit_visible=False,
                edit_enabled=False,
                edit_text="Pracovat s vybraným listem",
                edit_tooltip="",
                select_text="Načíst",
                select_enabled=True,
                select_tooltip="",
            ),
        )
        self._dot.setStyleSheet(_DOT_STYLE.format(color=ui.color))
        self._status_label.setText(ui.status_text)
        self._status_label.setToolTip(ui.status_tooltip)

        self._edit_selected_btn.setVisible(ui.edit_visible)
        self._edit_selected_btn.setEnabled(ui.edit_enabled)
        self._edit_selected_btn.setText(ui.edit_text)
        self._edit_selected_btn.setToolTip(ui.edit_tooltip)

        self._select_other_btn.setText(ui.select_text)
        self._select_other_btn.setEnabled(ui.select_enabled)
        self._select_other_btn.setToolTip(ui.select_tooltip)

        self._full_path = state.file_path if state.file_path else ""
        self._update_path_label()
        self.status_changed.emit()

    def _update_path_label(self) -> None:
        if not self._full_path:
            self._path_label.clear()
            self._path_label.setToolTip("")
            return
        self._path_label.setToolTip(self._full_path)
        elided = self._path_label.fontMetrics().elidedText(
            self._full_path,
            Qt.TextElideMode.ElideMiddle,
            self._path_label.width(),
        )
        self._path_label.setText(elided)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._update_path_label()

    def _on_select_other_clicked(self) -> None:
        context = self._build_load_context_from_new_selection()
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

    def _on_edit_selected_clicked(self) -> None:
        state = self._controller.get_table_state(self._table_key)
        status = state.status

        if status in {TableStatus.EMPTY, TableStatus.BROKEN_PATH}:
            QMessageBox.information(
                self,
                "Vybraná tabulka",
                "Nejprve vyberte platný soubor tabulky.",
            )
            self.refresh()
            return

        if status in {TableStatus.FILE_SELECTED, TableStatus.BROKEN_SHEET}:
            context = self._build_load_context_for_new_sheet_in_current_file()
            if context is None:
                return

            self._controller.set_sheet(self._table_key, context.sheet_name)

            if self._try_auto_apply_reusable_mapping(context):
                self._finalize_success(context.df)
                return

            if self._open_mapping_dialog_and_apply(context):
                self._finalize_success(context.df)
                return

            self.refresh()
            return

        context = self._build_load_context_from_current_selection()
        if context is None:
            return

        if self._open_mapping_dialog_and_apply(context):
            self._finalize_success(context.df)
            return

        self.refresh()

    def _build_load_context_for_new_sheet_in_current_file(
        self,
    ) -> TableLoadContext | None:
        state = self._controller.get_table_state(self._table_key)
        if not state.file_path:
            QMessageBox.information(
                self,
                "Vybraná tabulka",
                "Nejprve vyberte soubor tabulky.",
            )
            self.refresh()
            return None

        previous_mapping = dict(state.column_mapping)
        file_path = state.file_path
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

    def _build_load_context_from_new_selection(self) -> TableLoadContext | None:
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

    def _build_load_context_from_current_selection(self) -> TableLoadContext | None:
        state = self._controller.get_table_state(self._table_key)
        if not state.file_path or not state.sheet_name:
            QMessageBox.information(
                self,
                "Vybraná tabulka",
                "Nejprve vyberte soubor a list tabulky.",
            )
            self.refresh()
            return None

        previous_mapping = dict(state.column_mapping)
        file_path = state.file_path
        sheet_name = state.sheet_name

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
            return str(sheet_names[0])

        sheet_options = [str(name) for name in sheet_names]

        selected, ok = QInputDialog.getItem(
            self,
            "Výběr listu",
            "Vyberte list tabulky:",
            sheet_options,
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer != QMessageBox.StandardButton.Yes:
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
        if dialog.exec() != QDialog.DialogCode.Accepted:
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
            self._table_key == TableKey.SCHEDULE.value
            and self._on_schedule_preview_changed is not None
        ):
            self._on_schedule_preview_changed(df)
        self.refresh()
