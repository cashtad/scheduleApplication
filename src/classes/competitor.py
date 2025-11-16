from dataclasses import dataclass, field



@dataclass
class Competitor:
    id: str
    count: int
    full_name_1: str
    full_name_2: str | None
    performances: None | list['Performance'] = field(default_factory=list)
