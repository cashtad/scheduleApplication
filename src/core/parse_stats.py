from dataclasses import dataclass, field


@dataclass
class EntityParseStats:
    parsed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def add_skip(self, message: str) -> None:
        self.skipped += 1
        self.errors.append(message)


@dataclass
class GraphBuildStats:
    competitions: EntityParseStats = field(default_factory=EntityParseStats)
    competitors: EntityParseStats = field(default_factory=EntityParseStats)
    jury: EntityParseStats = field(default_factory=EntityParseStats)
    performances: EntityParseStats = field(default_factory=EntityParseStats)

    def as_text(self) -> str:
        return (
            "Výsledky parsování:\n"
            f"• Soutěže: {self.competitions.parsed} (přeskočeno {self.competitions.skipped})\n"
            f"• Účastníci: {self.competitors.parsed} (přeskočeno {self.competitors.skipped})\n"
            f"• Porotci: {self.jury.parsed} (přeskočeno {self.jury.skipped})\n"
            f"• Vystoupení: {self.performances.parsed} (přeskočeno {self.performances.skipped})"
        )