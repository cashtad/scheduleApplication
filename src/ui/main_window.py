import sys
from datetime import datetime
from pathlib import Path

import yaml
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core import AppSession, TableSession, TABLE_KEYS
from data import GraphBuilder, ExcelTableLoader, TemplateStore
from expert_system import ExplanationGenerator, InferenceEngine
from .widgets import ReportPanel, TableLoadPanel
from paths import get_rules_config_path, get_reports_dir


class AnalysisWorker(QThread):
    """Background thread that runs the schedule analysis."""

    finished = Signal(object, str)  # (ScheduleAnalysisResult, report_path)
    error = Signal(str)

    def __init__(self, session, rules_config, report_path):
        super().__init__()
        self.session = session
        self.rules_config = rules_config
        self.report_path = report_path

    def run(self):
        try:
            graph = GraphBuilder().build(self.session)
            self.session.graph = graph
            engine = InferenceEngine(self.rules_config)
            result = engine.analyze_schedule(graph)
            self.session.last_result = result
            ExplanationGenerator().generate_html_report(result, str(self.report_path))
            self.finished.emit(result, str(self.report_path))
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    """Main application window for schedule analysis."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analýza rozvrhu tanečního konkurzu")

        # Load rules config
        rules_config_path = get_rules_config_path()
        if not rules_config_path.exists():
            QMessageBox.critical(
                None,
                "Chyba konfigurace",
                f"Soubor rules_config.yaml nebyl nalezen:\n{rules_config_path}\n\n"
                "Zkopírujte rules_config.yaml do složky vedle .exe souboru."
            )
            sys.exit(1)
        with open(rules_config_path, encoding="utf-8") as f:
            self.rules_config = yaml.safe_load(f)

        # Central session
        self._session = AppSession()
        self._worker: AnalysisWorker | None = None
        self._progress: QProgressDialog | None = None

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Four table panels
        self._panels: dict[str, TableLoadPanel] = {}
        for key in TABLE_KEYS:
            panel = TableLoadPanel(key, self._session, parent=central)
            panel.status_changed.connect(self._update_analyze_button)
            self._panels[key] = panel
            layout.addWidget(panel)

        # Button row: Reload + Analyze
        btn_row = QHBoxLayout()

        self._reload_btn = QPushButton("🔄  Obnovit data")
        self._reload_btn.setToolTip(
            "Znovu načte všechny soubory z disku (použijte po uložení změn v Excelu)."
        )
        self._reload_btn.clicked.connect(self._reload_all_tables)
        btn_row.addWidget(self._reload_btn)

        self._analyze_btn = QPushButton("▶  Spustit analýzu")
        self._analyze_btn.setEnabled(False)
        self._analyze_btn.clicked.connect(self._run_analysis)
        btn_row.addWidget(self._analyze_btn)

        layout.addLayout(btn_row)

        # Report panel (hidden until first successful analysis)
        self._report_panel = ReportPanel(parent=central)
        self._report_panel.hide()
        layout.addWidget(self._report_panel)

        # Restore previous session
        self._restore_session()

    # ------------------------------------------------------------------
    # Session restore
    # ------------------------------------------------------------------

    def _restore_session(self) -> None:
        store = TemplateStore()
        saved_paths = store.load_session_paths()
        for key in TABLE_KEYS:
            info = saved_paths.get(key)
            if info is None:
                continue
            file_path = info["file_path"]
            if not Path(file_path).exists():
                continue
            try:
                raw_df = ExcelTableLoader(path=file_path, sheet=info["sheet_name"]).load()
            except Exception:
                continue
            panel = self._panels[key]
            auto_mapping = store.try_auto_apply(key, list(raw_df.columns))
            if auto_mapping is not None:
                self._session.tables[key] = TableSession(
                    table_key=key,
                    file_path=file_path,
                    sheet_name=info["sheet_name"],
                    raw_df=raw_df,
                    column_mapping=auto_mapping,
                )
                panel.set_status("ready")
            else:
                panel.set_status("needs_mapping")
                panel.pending_df = raw_df
                panel.pending_path = file_path
                panel.pending_sheet = info["sheet_name"]

        self._update_analyze_button()

    # ------------------------------------------------------------------
    # Reload all tables from disk (called by "Obnovit data" button)
    # ------------------------------------------------------------------

    def _reload_all_tables(self) -> None:
        """Re-read all previously loaded files from disk without changing mappings.

        Useful after editing and saving Excel files while the app is open.
        Tables that were not yet loaded are skipped silently.
        Tables whose file no longer exists show a warning.
        """
        store = TemplateStore()
        reloaded = 0
        failed = []

        for key in TABLE_KEYS:
            ts = self._session.tables.get(key)
            if ts is None:
                # Table was never loaded — nothing to reload
                continue

            if not Path(ts.file_path).exists():
                failed.append(ts.file_path)
                continue

            try:
                raw_df = ExcelTableLoader(path=ts.file_path, sheet=ts.sheet_name).load()
            except Exception as exc:
                failed.append(f"{ts.file_path} ({exc})")
                continue

            # Replace raw_df in-place, keep mapping and path unchanged
            self._session.tables[key] = TableSession(
                table_key=key,
                file_path=ts.file_path,
                sheet_name=ts.sheet_name,
                raw_df=raw_df,
                column_mapping=ts.column_mapping,
                selected_rows=ts.selected_rows,
            )
            reloaded += 1

        self._update_analyze_button()

        if failed:
            QMessageBox.warning(
                self,
                "Chyba při obnově dat",
                "Nepodařilo se znovu načíst:\n" + "\n".join(failed),
            )
        elif reloaded == 0:
            QMessageBox.information(
                self,
                "Obnovit data",
                "Žádné tabulky ještě nejsou načteny.",
            )
        else:
            QMessageBox.information(
                self,
                "Obnovit data",
                f"Úspěšně obnoveno {reloaded} tabulek z disku.",
            )

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _update_analyze_button(self) -> None:
        self._analyze_btn.setEnabled(self._session.is_ready_to_analyze())

    def _run_analysis(self) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        reports_dir = get_reports_dir()
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"schedule_report_{timestamp}.html"

        self._progress = QProgressDialog("Probíhá analýza rozvrhu...", None, 0, 0, self)
        self._progress.setWindowTitle("Analýza")
        self._progress.setModal(True)
        self._progress.show()

        self._worker = AnalysisWorker(self._session, self.rules_config, report_path)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_finished(self, result, report_path: str) -> None:
        if self._progress:
            self._progress.hide()
        self._session.last_result = result
        TemplateStore().save_session_paths(self._session)
        self._report_panel.update_report(report_path)
        self._report_panel.update_session(self._session)
        self._report_panel.show()

    def _on_analysis_error(self, error_message: str) -> None:
        if self._progress:
            self._progress.hide()
        QMessageBox.critical(
            self,
            "Chyba analýzy",
            f"Chyba při analýze:\n{error_message}",
        )
