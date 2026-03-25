from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base_human import Human


@dataclass(frozen=True, slots=True)
class Competitor(Human):
    participants_per_entry: int
    dancer_1_name: str
    dancer_2_name: Optional[str]

    def __str__(self) -> str:
        if self.participants_per_entry == 1:
            return f"Competitor {self.dancer_1_name}, participating in {self.competition_ids} competitions"
        return f"Pair of competitors {self.dancer_1_name} and {self.dancer_2_name}, participating in {self.competition_ids} competitions"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.participants_per_entry not in {1, 2}:
            raise ValueError("amount_of_people must be either 1 or 2")
        if not self.dancer_1_name.strip():
            raise ValueError("dancer_1_name cannot be empty")
        if self.participants_per_entry == 2 and (self.dancer_2_name is None or not self.dancer_2_name.strip()):
            raise ValueError("dancer_2_name cannot be empty when amount_of_people is 2")
        if self.participants_per_entry == 1 and self.dancer_2_name is not None and self.dancer_2_name.strip():
            raise ValueError("dancer_2_name must be empty for solo competitor")