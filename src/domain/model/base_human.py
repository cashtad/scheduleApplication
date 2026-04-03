from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True, slots=True)
class Human(ABC):
    competition_ids: FrozenSet[int]

    def __post_init__(self) -> None:
        if not self.competition_ids:
            raise ValueError("Pole 'competition_ids' nesmí být prázdné")
        if any(cid <= 0 for cid in self.competition_ids):
            raise ValueError("Všechna ID soutěží v 'competition_ids' musí být větší než nula")
