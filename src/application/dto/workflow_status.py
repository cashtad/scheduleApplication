from __future__ import annotations

from enum import Enum


class WorkflowStatus(Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
