from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .severity import Severity


@dataclass(frozen=True, slots=True)
class Violation:
    rule_name: str
    severity: Severity
    weight: float
    description: str
    entity_id: str
    entity_name: str
    details: dict[str, Any]
    source_rows: list[int] = field(default_factory=list)

    def dedup_key(self) -> tuple:
        details_items = tuple(sorted(self.details.items(), key=lambda x: x[0]))
        return (
            self.rule_name,
            self.severity.value,
            self.entity_id,
            self.entity_name,
            self.description,
            tuple(self.source_rows),
            details_items,
        )