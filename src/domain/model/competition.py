from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Competition:
    id: int
    name: str
    discipline: str
    participants_per_entry: int  # 1-more
    amount_of_rounds: int  # 1-more

    def __str__(self) -> str:
        return f"Competition #{self.id} - {self.name}"

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError("id must be greater than zero")
        if self.amount_of_rounds <= 0:
            raise ValueError("amount_of_rounds must be greater than zero")
        if self.participants_per_entry not in {1, 2}:
            raise ValueError("people_in_pair must be 1 or 2")
        if not self.discipline.strip():
            raise ValueError("discipline cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")