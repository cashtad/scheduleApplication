from dataclasses import dataclass, field




@dataclass
class Competition:
    """Vertex of graph: competition"""
    id: int
    name: str
    discipline: str
    age: str
    rank: str
    competitor_count: int
    round_count: int
    juries: list['Jury'] = field(default_factory=list)
    competitors: list['Competitor'] = field(default_factory=list)
    performances: list['Performance'] = field(default_factory=list)

    def __str__(self):
        text = f"Competition: {self.name}, juries: "

        for jury in self.juries:
            text += f"{jury.name}, "

        text += f", competitors: "

        for competitor in self.competitors:
            text += f"{competitor.full_name_1}, "

        return text
