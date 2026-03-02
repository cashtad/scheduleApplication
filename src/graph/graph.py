from src.classes.competition import Competition
from src.classes.competitor import Competitor
from src.classes.jury import Jury
from src.classes.performance import Performance


class ScheduleGraph:
    def __init__(self):
        self.competitors: list[Competitor] = []
        self.performances: list[Performance] = []
        self.juries: list[Jury] = []
        self.competitions: list[Competition] = []

    def get_competition_by_id(self, id: int) -> Competition | None:
        for competition in self.competitions:
            if competition.id == id:
                return competition
        return None

    def get_competitors(self):
        return self.competitors

    def get_juries(self):
        return self.juries

    def get_competitor_by_fullname(self, fullname) -> Competitor | None:
        for competitor in self.competitors:
            if competitor.full_name_1 == fullname or competitor.full_name_2 == fullname:
                return competitor
        return None

    def get_performances_by_fullname(self, fullname) -> list[Performance]:
        competitor = self.get_competitor_by_fullname(fullname)
        if competitor:
            return competitor.performances
        else:
            return []

