from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from application.dto import WorkflowStatus
from session import TableStatus
from .controllers import UiController


_TABLE_TITLES: dict[str, str] = {
    "competitions": "Soutěže",
    "competitors": "Účastníci",
    "jury": "Porotci",
    "schedule": "Rozvrh",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Analýza rozvrhu tanečního konkurzu")

        self._controller = UiController(
            rules_config_path=Path("rules_config.yaml"),
            reports_dir=".reports",
            with_html_report_writer=True,
        )

        self._table_buttons: dict[str, QPushButton] = {}
        self._status_labels: dict[str, QPushButton] = {}

        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        for table_key in self._controller.required_table_keys():
            row = QHBoxLayout()

            open_btn = QPushButton(f"Načíst: {_TABLE_TITLES.get(table_key, table_key)}")
            open_btn.clicked.connect(lambda _=False, k=table_key: self._on_open_table(k))
            self._table_buttons[table_key] = open_btn

            status_btn = QPushButton()
            status_btn.setEnabled(False)
            self._status_labels[table_key] = status_btn

            row.addWidget(open_btn)
            row.addWidget(status_btn)
            layout.addLayout(row)

        actions = QHBoxLayout()
        self._analyze_button = QPushButton("▶ Spustit analýzu")
        self._analyze_button.clicked.connect(self._on_run_analysis)
        actions.addWidget(self._analyze_button)
        layout.addLayout(actions)

        self._refresh_view_state()

    def _on_open_table(self, table_key: str) -> None:
        QMessageBox.information(
            self,
            "Další krok",
            f"Следующим шагом подключим полноценный TableLoadPanel для '{table_key}'",
        )

    def _on_run_analysis(self) -> None:
        result = self._controller.run_analysis()

        if result.status == WorkflowStatus.FAILED:
            QMessageBox.critical(self, "Chyba analýzy", result.error_message or "Neznámá chyba")
            self._refresh_view_state()
            return

        if result.status == WorkflowStatus.BLOCKED:
            reasons = result.quality_report.readiness_result.reasons
            text = "\n".join(f"- [{r.severity.value}] {r.code}: {r.message_en}" for r in reasons)
            QMessageBox.warning(self, "Analýza zablokována", text or "Analýza zablokována politikou kvality.")
            self._refresh_view_state()
            return

        html_path = result.html_report_path or "не был сгенерирован"
        QMessageBox.information(self, "Готово", f"Анализ завершён.\nHTML отчет: {html_path}")
        self._refresh_view_state()

    def _refresh_view_state(self) -> None:
        statuses = self._controller.get_table_statuses()
        for table_key, status in statuses.items():
            self._status_labels[table_key].setText(self._status_text(status))
        self._analyze_button.setEnabled(self._controller.can_run_analysis())

    @staticmethod
    def _status_text(status: TableStatus) -> str:
        return f"Status: {status.value}"