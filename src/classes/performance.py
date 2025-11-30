from dataclasses import dataclass
from datetime import datetime

from src.classes.competition import Competition


@dataclass
class Performance:
    """Vertex of graph: performance (round of competition"""
    start_time: datetime
    end_time: datetime
    duration: int
    competition: Competition
    round_type: str

    def __str__(self):
        text = f"Perfomance: {self.competition.name}-{self.round_type}  {self.start_time}-{self.end_time}"
        return text