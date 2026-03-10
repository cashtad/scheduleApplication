import json
from pathlib import Path
from typing import Optional
from paths import get_templates_dir


class TemplateStore:
    """Saves and loads column-mapping templates + last-used file paths."""

    def __init__(self, templates_dir: Path | None = None):
        self._dir = templates_dir or get_templates_dir()

    def _template_path(self, table_key: str) -> Path:
        return self._dir / f"{table_key}.json"

    def _read_json(self, table_key: str) -> Optional[dict]:
        path = self._template_path(table_key)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, table_key: str, data: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._template_path(table_key), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_mapping(self, table_key: str, mapping: dict, column_headers: list) -> None:
        """Save mapping template with a sample of column headers for future auto-matching."""
        existing = self._read_json(table_key) or {}
        existing["mapping"] = mapping
        existing["column_headers"] = column_headers
        self._write_json(table_key, existing)

    def load_mapping(self, table_key: str) -> Optional[dict]:
        """Load the last saved mapping for a table. Returns None if not found."""
        raw = self._read_json(table_key)
        if raw is None:
            return None
        return raw.get("mapping")

    def save_session_paths(self, session) -> None:
        """Persist file_path and sheet_name for all tables so next launch can restore them."""
        for table_key, ts in session.tables.items():
            raw = self._read_json(table_key) or {}
            raw["file_path"] = ts.file_path
            raw["sheet_name"] = ts.sheet_name
            self._write_json(table_key, raw)

    def load_session_paths(self) -> dict:
        """Load {table_key: {file_path, sheet_name}} dict from disk."""
        result = {}
        if not self._dir.exists():
            return result
        for path in self._dir.glob("*.json"):
            table_key = path.stem
            raw = self._read_json(table_key) or {}
            if "file_path" in raw:
                result[table_key] = {
                    "file_path": raw["file_path"],
                    "sheet_name": raw.get("sheet_name"),
                }
        return result

    def get_auto_mapping(self, table_key: str, df_columns: list) -> Optional[dict]:
        """
        If saved column headers match df_columns exactly, return saved mapping.
        Otherwise return None (user must re-map manually).
        """
        raw = self._read_json(table_key)
        if raw is None:
            return None
        saved_headers = raw.get("column_headers")
        if saved_headers is not None and list(saved_headers) == list(df_columns):
            return raw.get("mapping")
        return None