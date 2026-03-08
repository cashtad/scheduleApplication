from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True)
class Jury:
    name: str
    surname: str
    fullname: str
    competition_ids: FrozenSet[int]

    def __str__(self):
        return f"Jury member {self.fullname} for competitions {self.competition_ids}"
