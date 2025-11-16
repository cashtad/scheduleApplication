from src.classes.competition import Competition
from src.classes.competitor import Competitor
from src.classes.jury import Jury
from src.classes.performance import Performance
from src.config.config_loader import ConfigLoader
from src.parsers.competitions_table import CompetitionParser
from src.parsers.competitors_table import CompetitorsParser
from src.parsers.excel_loader import ExcelTableLoader
from src.parsers.jury_table import JuryParser
from src.parsers.schedule_table import PerformanceParser


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

    def fill_with_data(self, config_path: str):
        cfg = ConfigLoader(config_path).load()

        competitions_df = ExcelTableLoader(**cfg.files["competitions"]).load()
        registered_df = ExcelTableLoader(**cfg.files["competitors"]).load()
        jury_df = ExcelTableLoader(**cfg.files["jury"]).load()
        schedule_df = ExcelTableLoader(**cfg.files["schedule"]).load()

        self.competitions = CompetitionParser(cfg.columns["competitions"]).parse(competitions_df)

        performances = PerformanceParser(cfg.columns["schedule"]).parse(schedule_df)
        for performance, competition_id in performances:
            competition = self.get_competition_by_id(competition_id)
            if competition:
                competition.performances.append(performance)
                performance.competition = competition
            else :
                print(f"Competition with id {competition_id} not found")
            self.performances.append(performance)

        juries = JuryParser(cfg.columns["jury"]).parse(jury_df)

        for jury, assignments in juries:
            for competition_id in assignments:
                competition = self.get_competition_by_id(competition_id)
                if competition:
                    competition.juries.append(jury)
                else:
                    print(f"Competition with id {competition_id} not found")
                jury.performances.append(competition)
            self.juries.append(jury)

        competitors = CompetitorsParser(cfg.columns["competitors"]).parse(registered_df)

        for pairs in competitors:
            competitor = pairs[0]
            competitions = pairs[1]

            for competition_id in competitions:
                competition = self.get_competition_by_id(competition_id)
                if competition:
                    competition.competitors.append(competitor)
                else:
                    print(f"Competition with id {competition_id} not found")
                competitor.performances.append(competition)
            self.competitors.append(competitor)

        print("Data filled")

