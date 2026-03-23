from abc import ABC


class Human(ABC):
    competition_ids: FrozenSet[int]