"""
Central path resolution for both development and frozen (.exe) modes.

When frozen (PyInstaller), all persistent files live next to the .exe.
When running as plain Python, they live in src/config/ (existing layout).
"""
import sys
from pathlib import Path


def _is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def get_data_dir() -> Path:
    """
    Returns the directory where all user-editable and runtime files live:
      - rules_config.yaml
      - templates/ (JSON mapping templates)
      - schedule_report_*.html (output reports)

    Frozen (.exe): folder containing the .exe
    Dev:           <repo_root>/src/config/
    """
    if _is_frozen():
        return Path(sys.executable).parent
    # dev: src/paths.py -> src/ -> src/config
    return Path(__file__).parent / "config"


def get_rules_config_path() -> Path:
    return get_data_dir() / "rules_config.yaml"


def get_templates_dir() -> Path:
    return get_data_dir() / "templates"


def get_reports_dir() -> Path:
    """Reports go next to the .exe (or src/config/ in dev)."""
    return get_data_dir()