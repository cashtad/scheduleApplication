from dataclasses import dataclass, field



@dataclass
class Competitor:
    id: str
    count: int
    full_name_1: str
    full_name_2: str | None
    performances: None | list['Performance'] = field(default_factory=list)

    def __str__(self):
        text = f"Competitor: {self.full_name_1} {self.full_name_2} amount of performances: {self.performances.__len__()}"
        return text


