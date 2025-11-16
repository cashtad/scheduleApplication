from dataclasses import dataclass, field
from datetime import datetime

from src.classes.competition import Competition


@dataclass
class Performance:
    """Узел графа: выступление (раунд соревнования)"""
    start_time: datetime
    end_time: datetime
    duration: int  # in minutes
    competition: Competition | None
    round_type: str

    def __str__(self):
        text = f"Perfomance: {self.round_type} {self.start_time}-{self.end_time}"
        return text