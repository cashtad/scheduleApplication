from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True, slots=True)
class Human(ABC):
    competition_ids: FrozenSet[int]

    def __post_init__(self) -> None:
        if not self.competition_ids:
            raise ValueError("competition_ids cannot be empty")
        if any(cid <= 0 for cid in self.competition_ids):
            raise ValueError("All competition_ids must be greater than zero")
