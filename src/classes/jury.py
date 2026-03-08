from dataclasses import dataclass


@dataclass(frozen=True)
class Jury:
    name: str
    surname: str
    fullname: str
    competition_ids: set[int]

    def __str__(self):
        return f"Jury member {self.fullname} for competitions {self.competition_ids}"
