from enum import Enum


class Severity(Enum):
    """Severity level of rule violation"""
    CRITICAL = "critical"
    MEDIUM = "medium"
    LOW = "low"
