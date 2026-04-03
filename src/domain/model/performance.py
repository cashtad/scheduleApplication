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
            raise ValueError("Pole 'duration' musí být větší než nula")
        if self.end_time <= self.start_time:
            raise ValueError("Pole 'end_time' musí být později než 'start_time'")
        if timedelta(minutes=self.duration) != self.end_time - self.start_time:
            raise ValueError("Pole 'duration' musí odpovídat rozdílu end_time - start_time")
        if not self.round_type.strip():
            raise ValueError("Pole 'round_type' nesmí být prázdné")
        if self.competition_id <= 0:
            raise ValueError("Pole 'competition_id' musí být větší než nula")
        if self.source_row < 0:
            raise ValueError("Pole 'source_row' nesmí být záporné")
