from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from ..model import Human, JuryMember, Competitor, Competition, Performance


@dataclass(frozen=True, slots=True)
class RepositoryBuildError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


class ScheduleRepository:
    def __init__(self) -> None:
        self._competitions_by_id: dict[int, Competition] = {}
        self._performances_by_competition_id: dict[int, list[Performance]] = defaultdict(list)
        self._jury_members: set[JuryMember] = set()
        self._competitors: set[Competitor] = set()

    @property
    def competitions_by_id(self) -> dict[int, Competition]:
        return self._competitions_by_id

    @property
    def jury_members(self) -> set[JuryMember]:
        return self._jury_members

    @property
    def competitors(self) -> set[Competitor]:
        return self._competitors

    @property
    def performances_by_competition_id(self) -> dict[int, list[Performance]]:
        return self._performances_by_competition_id

    def add_competition(self, competition: Competition) -> None:
        if competition.id in self._competitions_by_id:
            raise RepositoryBuildError(f"Competition with id={competition.id} already exists")
        self._competitions_by_id[competition.id] = competition

    def add_competitions(self, competitions: Iterable[Competition]) -> None:
        for competition in competitions:
            self.add_competition(competition)

    def add_performance(self, performance: Performance) -> None:
        self._performances_by_competition_id[performance.competition_id].append(performance)

    def add_performances(self, performances: Iterable[Performance]) -> None:
        for performance in performances:
            self.add_performance(performance)

    def add_jury_member(self, jury_member: JuryMember) -> None:
        self._jury_members.add(jury_member)

    def add_jury_members(self, jury_members: Iterable[JuryMember]) -> None:
        for jury_member in jury_members:
            self.add_jury_member(jury_member)

    def add_competitor(self, competitor: Competitor) -> None:
        self._competitors.add(competitor)

    def add_competitors(self, competitors: Iterable[Competitor]) -> None:
        for competitor in competitors:
            self.add_competitor(competitor)

    def find_competition_by_id(self, competition_id: int) -> Competition | None:
        return self._competitions_by_id.get(competition_id)

    def list_performances_by_competition_id(self, competition_id: int) -> list[Performance]:
        return list(self._performances_by_competition_id.get(competition_id, []))

    def list_assignments_of_human(self, human: Human) -> list[Performance]:
        performances: list[Performance] = []
        for competition_id in human.competition_ids:
            performances.extend(self.list_performances_by_competition_id(competition_id))
        return sorted(performances, key=lambda p: p.start_time)
