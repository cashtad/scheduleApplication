from __future__ import annotations

from enum import Enum


class IngestionSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"