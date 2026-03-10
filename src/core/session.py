from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from .table_config import TABLE_CONFIGS


@dataclass
class TableSession:
    """State of one loaded table"""
    table_key: str                         # one of TABLE_CONFIGS.keys()
    file_path: str                         # absolute path chosen by user
    sheet_name: Optional[str]             # selected sheet name (None = first sheet)
    raw_df: Optional[pd.DataFrame] = None
    column_mapping: dict[str, str] = field(default_factory=dict)  # logical_name → real_column_name
    selected_rows: Optional[list] = None  # None means all rows


@dataclass
class AppSession:
    """Central application context — single source of truth"""
    tables: dict[str, TableSession] = field(default_factory=dict)
    graph: Optional[object] = None   # ScheduleGraph, set after build
    last_result: Optional[object] = None  # ScheduleAnalysisResult, set after analysis

    def is_ready_to_analyze(self) -> bool:
        """Returns True when all 4 tables are loaded and mapped"""
        return all(
            k in self.tables
            and self.tables[k].raw_df is not None
            and bool(self.tables[k].column_mapping)
            for k in TABLE_CONFIGS.keys()
        )

    def get_table(self, key: str) -> Optional[TableSession]:
        """Return the TableSession for *key*, or None if not yet loaded."""
        return self.tables.get(key)

