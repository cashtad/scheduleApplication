from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True, slots=True)
class JuryMember(Human):
    fullname: str

    def __str__(self):
        return f"Jury member {self.fullname} for competitions {self.competition_ids}"

    def __post_init__(self):
        if self.fullname.strip() == "":
            raise ValueError("Full name cannot be empty")
