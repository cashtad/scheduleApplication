from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Competition:
    id: int
    name: str
    discipline: str
    people_in_pair: int  # 1-more
    amount_of_rounds: int  # 1-more

    def __str__(self):
        return f"Competition #{self.id} - {self.name}"

    def __post_init__(self):
        if self.id < 0:
            raise ValueError("Competition id cannot be negative")
        if self.amount_of_rounds < 0:
            raise ValueError("Amount of rounds cannot be negative")
        if self.people_in_pair < 0:
            raise ValueError("People in pair amount cannot be negative")
        if self.people_in_pair not in {1, 2}:
            raise ValueError("People in pair amount must be 1 or 2")
        if self.discipline.strip() == "":
            raise ValueError("Discipline cannot be empty")
        if self.name.strip() == "":
            raise ValueError("Name cannot be empty")
