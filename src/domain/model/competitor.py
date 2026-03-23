from dataclasses import dataclass
from typing import Optional, FrozenSet


@dataclass(frozen=True, slots=True)
class Competitor(Human):
    amount_of_people: int
    dancer_1_name: str
    dancer_2_name: Optional[str]

    def __str__(self):
        if self.amount_of_people == 1:
            return f"Competitor {self.dancer_1_name}, participating in {self.competition_ids} competitions"
        else:
            return f"Pair of competitors {self.dancer_1_name} and {self.dancer_2_name}, participating in {self.competition_ids} competitions"

    def __post_init__(self):
        if self.amount_of_people not in {1, 2}:
            raise ValueError(f"Count must be either 1 or 2")
        if self.dancer_1_name.strip() == "":
            raise ValueError(f"Full name cannot be empty")
        if self.amount_of_people == 2 and (self.dancer_2_name is None or self.dancer_2_name.strip() == ""):
            raise ValueError(f"Full name of second competitor cannot be empty when amount of people is 2")
