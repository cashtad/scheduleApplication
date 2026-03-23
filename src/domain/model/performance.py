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

    def __str__(self):
        return f"Performance linked to competition #{self.competition_id} {self.round_type} {self.start_time}-{self.end_time}"

    def __post_init__(self):
        if timedelta(minutes=self.duration) != self.end_time - self.start_time:
            raise ValueError("Duration must match the difference between end_time and start_time")
        if self.round_type.strip() == "":
            raise ValueError("Round type cannot be empty")
        if self.competition_id < 0:
            raise ValueError("Competition id cannot be negative")
        if self.source_row < 0:
            raise ValueError("Source row cannot be negative")
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
