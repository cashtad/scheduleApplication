from dataclasses import dataclass


@dataclass(frozen=True)
class Competition:
    id: int
    name: str
    discipline: str
    age: str  # jun (I- III) etc
    rank: str  # sil, gold etc
    competitor_count: int  # 1-2
    round_count: int  # 1-more

    def __str__(self):
        return f"Competition #{self.id} - {self.name}"
