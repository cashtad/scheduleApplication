from ..model import Human, JuryMember, Competitor, Competition, Performance


class ScheduleRepository:
    def __init__(self):
        self.competitions_by_id: dict[int, Competition] = {}
        self.performances_by_competition_id: dict[int, set[Performance]] = {}
        # self.jury_members_by_competition_id = dict[int, set[JuryMember]]
        #TODO: mb add additional dicts
        self.jury_members: set[JuryMember] = set()
        self.competitors: set[Competitor] = set()

    def add_competition(self, competition: Competition):
        if competition.id not in self.competitions_by_id.keys():
            self.competitions_by_id[competition.id] = competition
        else:
            raise Exception(f"Competition with id {competition.id} already exists")

    def add_performance(self, performance: Performance):
        if performance.competition_id not in self.competitions_by_id.keys():
            raise Exception(f"Competition with id {performance.competition_id} does not exist")
        if performance.competition_id not in self.performances_by_competition_id.keys():
            self.performances_by_competition_id[performance.competition_id] = set()
        self.performances_by_competition_id[performance.competition_id].add(performance)

    def add_jury_member(self, jury_member: JuryMember):
        self.jury_members.add(jury_member)

    def add_competitor(self, competitor: Competitor):
        self.competitors.add(competitor)

    def find_competition_by_id(self, competition_id: int) -> Competition | None:
        return self.competitions_by_id.get(competition_id, None)

    def find_performances_by_competition_id(self, competition_id: int) -> list[Performance] | None:
        return self.performances_by_competition_id.get(competition_id, None)

    def find_assignments_of_human(self, human: Human) -> list[Performance] | None:
        result = list[Performance]()
        for competition_id in human.competition_ids:
            result.extend(self.find_performances_by_competition_id(competition_id))
        return result


