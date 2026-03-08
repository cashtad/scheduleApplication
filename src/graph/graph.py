from typing import Optional

from classes import Competition, Competitor, Jury, Performance


class ScheduleGraph:
    def __init__(self):
        self.competitors: set[Competitor] = set()
        self.performances: set[Performance] = set()
        self.juries: set[Jury] = set()
        self.competitions: set[Competition] = set()

    def set_competitors(self, competitors: set[Competitor]):
        self.competitors = competitors

    def get_competitors(self):
        return self.competitors

    def get_competitor_by_fullname(self, fullname) -> Optional[Competitor]:
        for competitor in self.competitors:
            if competitor.full_name_1 == fullname or competitor.full_name_2 == fullname:
                return competitor
        return None

    def set_juries(self, juries: set[Jury]):
        self.juries = juries

    def get_juries(self):
        return self.juries

    def get_jury_by_fullname(self, fullname) -> Optional[Jury]:
        for jury in self.juries:
            if jury.full_name == fullname:
                return jury
        return None

    def set_competitions(self, competitions: set[Competition]):
        self.competitions = competitions

    def get_competitions(self):
        return self.competitions

    def get_competition_by_id(self, id: int) -> Optional[Competition]:
        for competition in self.competitions:
            if competition.id == id:
                return competition
        return None

    def set_performances(self, performances: set[Performance]):
        self.performances = performances

    def get_performances(self):
        return self.performances

    def get_performances_of_competitor_by_fullname(self, fullname) -> set[Performance]:
        competitor = self.get_competitor_by_fullname(fullname)
        if competitor:
            return set(p for p in self.performances if p.competition_id in competitor.competition_ids)
        else:
            return set()

    def get_performances_of_jury_by_fullname(self, fullname) -> set[Performance]:
        jury = next((j for j in self.juries if j.full_name == fullname), None)
        if jury:
            return set(p for p in self.performances if p.jury_id == jury.id)
        else:
            return set()
    def get_performances_by_competition_ids(self, competition_ids: set[int]) -> set[Performance]:
        return set(p for p in self.performances if p.competition_id in competition_ids)

