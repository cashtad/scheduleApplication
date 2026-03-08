TABLE_KEYS = ["competitions", "competitors", "jury", "schedule"]

from .session import AppSession, TableSession

__all__ = ["AppSession", "TableSession", "TABLE_KEYS"]
