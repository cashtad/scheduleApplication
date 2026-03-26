from __future__ import annotations

from enum import Enum


class TableStatus(Enum):
    EMPTY = "empty"
    FILE_SELECTED = "file_selected"
    SHEET_SELECTED = "sheet_selected"
    MAPPED = "mapped"
    READY = "ready"
    BROKEN_PATH = "broken_path"
    BROKEN_SHEET = "broken_sheet"
    MAPPING_STALE = "mapping_stale"