from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class Performance:
    start_time: datetime
    end_time: datetime
    duration: int  # duration in minutes
    round_type: str  # "semifinal", "final", etc.
    competition_id: int  # ID of the linked competition, None if not linked
    source_row: int  # Row index in the original schedule DataFrame

    def __str__(self) -> str:
        return f"Performance linked to competition #{self.competition_id} {self.round_type} {self.start_time}-{self.end_time}"

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("duration must be greater than zero")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        if timedelta(minutes=self.duration) != self.end_time - self.start_time:
            raise ValueError("duration must match end_time - start_time")
        if not self.round_type.strip():
            raise ValueError("round_type cannot be empty")
        if self.competition_id <= 0:
            raise ValueError("competition_id must be greater than zero")
        if self.source_row < 0:
            raise ValueError("source_row cannot be negative")
