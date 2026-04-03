from __future__ import annotations

from dataclasses import dataclass

from .base_human import Human


@dataclass(frozen=True, slots=True)
class JuryMember(Human):
    fullname: str

    def __str__(self) -> str:
        return f"Jury member {self.fullname} for competitions {self.competition_ids}"

    def __post_init__(self) -> None:
        super(JuryMember, self).__post_init__()
        if not self.fullname.strip():
            raise ValueError("Pole 'fullname' nesmí být prázdné")
