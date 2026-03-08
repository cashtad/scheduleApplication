from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Performance:
    start_time: datetime
    end_time: datetime
    duration: int  # duration in minutes
    round_type: str  # "semifinal", "final", etc.
    competition_id: int  # ID of the linked competition, None if not linked
    source_row: int  # Row index in the original schedule DataFrame

    def __str__(self):
        return f"Performance linked to competition #{self.competition_id} {self.round_type} {self.start_time}-{self.end_time}"
