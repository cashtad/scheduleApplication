from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .session_store import PersistedSession, PersistedTableState, SessionStore

try:
    from platformdirs import user_data_dir
except Exception:
    user_data_dir = None


class JsonSessionStore(SessionStore):
    def __init__(self, app_name: str = "DanceScheduleAnalyzer", app_author: str = "Leonid Malakhov") -> None:
        self._path = JsonSessionStore._resolve_session_path(app_name=app_name, app_author=app_author)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> PersistedSession | None:
        if not self._path.exists():
            return None

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Corrupted session file -> ignore and start fresh
            return None
        except OSError:
            return None

        tables_raw = raw.get("tables", {})
        tables: dict[str, PersistedTableState] = {}
        for table_key, payload in tables_raw.items():
            tables[table_key] = PersistedTableState(
                file_path=payload.get("file_path"),
                sheet_name=payload.get("sheet_name"),
                column_mapping=dict(payload.get("column_mapping", {})),
                column_signature=list(payload.get("column_signature", [])),
            )

        return PersistedSession(
            version=int(raw.get("version", 1)),
            saved_at=raw.get("saved_at"),
            tables=tables,
        )

    def save(self, session: PersistedSession) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": session.version,
            "saved_at": session.saved_at or datetime.now(timezone.utc).isoformat(),
            "tables": {k: asdict(v) for k, v in session.tables.items()},
        }

        self._atomic_write_json(self._path, payload)

    @staticmethod
    def _resolve_session_path(app_name: str, app_author: str) -> Path:
        if user_data_dir is not None:
            try:
                base = Path(user_data_dir(app_name=app_name, appauthor=app_author))
                return base / "session.json"
            except Exception:
                pass
        return Path(".app_data") / "session.json"

    @staticmethod
    def _atomic_write_json(path: Path, payload: dict) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_name = tmp.name
        Path(temp_name).replace(path)