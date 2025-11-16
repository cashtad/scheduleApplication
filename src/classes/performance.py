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

