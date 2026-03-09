import json
from pathlib import Path
from typing import Optional
from paths import get_templates_dir


class TemplateStore:
    """Saves and loads column-mapping templates + last-used file paths."""

    @staticmethod
    def _template_path(table_key: str) -> Path:
        return get_templates_dir() / f"{table_key}.json"

    def _load_raw(self, table_key: str) -> Optional[dict]:
        path = self._template_path(table_key)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _save_raw(self, table_key: str, data: dict) -> None:
        get_templates_dir().mkdir(parents=True, exist_ok=True)
        with open(self._template_path(table_key), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_mapping(self, table_key: str, mapping: dict, column_headers: list) -> None:
        """Save mapping template with a sample of column headers for future auto-matching."""
        existing = self._load_raw(table_key) or {}
        existing["mapping"] = mapping
        existing["column_headers"] = column_headers
        self._save_raw(table_key, existing)

    def load_mapping(self, table_key: str) -> Optional[dict]:
        """Load the last saved mapping for a table. Returns None if not found."""
        raw = self._load_raw(table_key)
        if raw is None:
            return None
        return raw.get("mapping")

    def save_session_paths(self, session) -> None:
        """Persist file_path and sheet_name for all tables so next launch can restore them."""
        for table_key, ts in session.tables.items():
            raw = self._load_raw(table_key) or {}
            raw["file_path"] = ts.file_path
            raw["sheet_name"] = ts.sheet_name
            self._save_raw(table_key, raw)

    def load_session_paths(self) -> dict:
        """Load {table_key: {file_path, sheet_name}} dict from disk."""
        result = {}
        templates_dir = get_templates_dir()
        if not templates_dir.exists():
            return result
        for path in templates_dir.glob("*.json"):
            table_key = path.stem
            raw = self._load_raw(table_key) or {}
            if "file_path" in raw:
                result[table_key] = {
                    "file_path": raw["file_path"],
                    "sheet_name": raw.get("sheet_name"),
                }
        return result

    def try_auto_apply(self, table_key: str, df_columns: list) -> Optional[dict]:
        """
        If saved column headers match df_columns exactly, return saved mapping.
        Otherwise return None (user must re-map manually).
        """
        raw = self._load_raw(table_key)
        if raw is None:
            return None
        saved_headers = raw.get("column_headers")
        if saved_headers is not None and list(saved_headers) == list(df_columns):
            return raw.get("mapping")
        return None