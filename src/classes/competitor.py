from dataclasses import dataclass
from typing import Optional, FrozenSet


@dataclass(frozen=True)
class Competitor:
    count: int
    full_name_1: str
    full_name_2: Optional[str]
    competition_ids: FrozenSet[int]

    def __str__(self):
        if self.count == 1:
            return f"Competitor {self.full_name_1}, participating in {self.competition_ids} competitions"
        else:
            return f"Pair of competitors {self.full_name_1} and {self.full_name_2}, participating in {self.competition_ids} competitions"
