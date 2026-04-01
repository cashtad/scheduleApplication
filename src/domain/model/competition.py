from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Competition:
    id: int
    name: str
    discipline: str
    amount_of_rounds: int  # 1-more

    def __str__(self) -> str:
        return f"Competition #{self.id} - {self.name}"

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError("id must be greater than zero")
        if self.amount_of_rounds < 0:
            raise ValueError("amount_of_rounds must be positive integer")
        if not self.discipline.strip():
            raise ValueError("discipline cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
