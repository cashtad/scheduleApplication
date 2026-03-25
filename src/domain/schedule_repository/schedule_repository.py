from __future__ import annotations

from collections import defaultdict

from ..model import Human, JuryMember, Competitor, Competition, Performance


class ScheduleRepository:
    def __init__(self) -> None:
        self.competitions_by_id: dict[int, Competition] = {}
        self.performances_by_competition_id: dict[int, list[Performance]] = defaultdict(list)
        self.jury_members: set[JuryMember] = set()
        self.competitors: set[Competitor] = set()

    def add_competition(self, competition: Competition):
        if competition.id not in self.competitions_by_id:
            self.competitions_by_id[competition.id] = competition
        # else:
        #     raise Exception(f"Competition with id {competition.id} already exists")

    def add_performance(self, performance: Performance) -> None:
        self.performances_by_competition_id[performance.competition_id].append(performance)

    def add_jury_member(self, jury_member: JuryMember) -> None:
        self.jury_members.add(jury_member)

    def add_competitor(self, competitor: Competitor) -> None:
        self.competitors.add(competitor)

    def find_competition_by_id(self, competition_id: int) -> Competition | None:
        return self.competitions_by_id.get(competition_id)

    def find_performances_by_competition_id(self, competition_id: int) -> list[Performance]:
        return list(self.performances_by_competition_id.get(competition_id, []))

    def list_assignments_of_human(self, human: Human) -> list[Performance]:
        result: list[Performance] = []
        for competition_id in human.competition_ids:
            result.extend(self.find_performances_by_competition_id(competition_id))
        return sorted(result, key=lambda p: p.start_time)