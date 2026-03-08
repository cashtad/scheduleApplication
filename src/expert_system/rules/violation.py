from dataclasses import dataclass, field
from typing import Any

from .severity import Severity


@dataclass
class Violation:
    """Rule violation with all relevant information"""
    rule_name: str  # Name of the violated rule
    severity: Severity  # Severity level
    weight: float  # Calculated weight of violation
    description: str  # Human-readable description
    entity_id: str  # ID of dancer/judge involved
    entity_name: str  # Name of dancer/judge
    details: dict[str, Any]  # Additional details about the violation
    source_rows: list[int] = field(default_factory=list)  # Row indices in schedule DataFrame
