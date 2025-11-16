from dataclasses import dataclass, field



@dataclass
class Jury:
    """Узел графа: судья"""
    id: str
    name: str
    performances: None | list['Performance'] = field(default_factory=list)
