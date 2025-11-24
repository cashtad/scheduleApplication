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

    def get_competitors(self):
        return self.competitors

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


    def fill_with_data(self, config_path: str):
        cfg = ConfigLoader(config_path).load()

        competitions_df = ExcelTableLoader(**cfg.files["competitions"]).load()
        registered_df = ExcelTableLoader(**cfg.files["competitors"]).load()
        jury_df = ExcelTableLoader(**cfg.files["jury"]).load()
        schedule_df = ExcelTableLoader(**cfg.files["schedule"]).load()


        # Simple parse of competitions, they are currently not linked to any other table
        self.competitions = CompetitionParser(cfg.columns["competitions"]).parse(competitions_df)


        # Connecting performances to competitions
        performances = PerformanceParser(cfg.columns["schedule"]).parse(schedule_df)
        for performance, competition_id in performances:
            competition = self.get_competition_by_id(competition_id)
            if competition:
                competition.performances.append(performance)
                performance.competition = competition
            else :
                print(f"Competition with id {competition_id} not found")
            self.performances.append(performance)

        # Connecting judges to competitions
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

        # Connecting competitors to competitions
        dancers = CompetitorsParser(cfg.columns["competitors"]).parse(registered_df)
        for pairs in dancers:
            dancer = pairs[0]
            competitions = pairs[1]


            for competition_id in competitions:
                competition = self.get_competition_by_id(competition_id)
                if competition:
                    competition.competitors.append(dancer)
                else:
                    print(f"Competition with id {competition_id} not found")
                for performance in competition.performances:
                    dancer.performances.append(performance)
            self.competitors.append(dancer)

        print("Data filled")

