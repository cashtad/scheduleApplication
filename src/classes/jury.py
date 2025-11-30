from dataclasses import dataclass, field



@dataclass
class Jury:
    """Vertex of graph: jury"""
    id: str
    name: str
    performances: None | list['Performance'] = field(default_factory=list)
