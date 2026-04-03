from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work when running `python src/main.py`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication

from src.presentation.qt.main_window import MainWindow


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--smoke-startup",
        action="store_true",
        help="Initialize QApplication and MainWindow, then exit immediately.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    if args.smoke_startup:
        print("SMOKE_STARTUP_OK")
        window.close()
        app.quit()
        return 0

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())