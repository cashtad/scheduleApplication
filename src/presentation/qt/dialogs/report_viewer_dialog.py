import webbrowser

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView

    HAS_WEBENGINE = True
except ImportError:
    from PySide6.QtWebEngineWidgets import QWebEngineView

    HAS_WEBENGINE = False


class ReportViewerDialog(QDialog):
    """Dialog that displays the generated HTML report."""

    def __init__(self, report_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zpráva o analýze rozvrhu")
        self.resize(960, 720)

        layout = QVBoxLayout(self)

        if HAS_WEBENGINE:
            self._view = QWebEngineView()
            self._view.load(QUrl.fromLocalFile(report_path))
            layout.addWidget(self._view)
        else:
            label = QLabel("Prohlížeč v aplikaci není dostupný.")
            layout.addWidget(label)
            webbrowser.open(f"file://{report_path}")
            self.accept()
            return

        close_btn = QPushButton("Zavřít")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
