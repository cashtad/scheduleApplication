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
            raise ValueError("Pole 'id' musí být větší než nula")
        if self.amount_of_rounds < 0:
            raise ValueError("Pole 'amount_of_rounds' musí být kladné celé číslo")
        if not self.discipline.strip():
            raise ValueError("Pole 'discipline' nesmí být prázdné")
        if not self.name.strip():
            raise ValueError("Pole 'name' nesmí být prázdné")
