from src.core.session import AppSession
from src.graph.graph import ScheduleGraph
from src.parsers.competitions_table import CompetitionParser
from src.parsers.competitors_table import CompetitorsParser
from src.parsers.jury_table import JuryParser
from src.parsers.schedule_table import PerformanceParser


class GraphBuilder:
    """Builds ScheduleGraph from AppSession.
    Does NOT read files — uses already-loaded DataFrames from session."""

    def build(self, session: AppSession) -> ScheduleGraph:
        """
        Takes session.tables["competitions"].raw_df + .column_mapping,
        same for competitors, jury, schedule —
        applies column_mapping to filter/rename columns,
        uses existing parsers (CompetitionParser, CompetitorsParser, JuryParser, PerformanceParser),
        builds and returns a ScheduleGraph.

        If TableSession.selected_rows is not None, slice the DataFrame to those rows before parsing.
        """
        graph = ScheduleGraph()

        def get_df(key):
            ts = session.tables[key]
            df = ts.raw_df
            if ts.selected_rows is not None:
                df = df.loc[ts.selected_rows]
            return df

        competitions_df = get_df("competitions")
        competitors_df = get_df("competitors")
        jury_df = get_df("jury")
        schedule_df = get_df("schedule")

        # Parse competitions
        graph.competitions = CompetitionParser(
            session.tables["competitions"].column_mapping
        ).parse(competitions_df)

        # Connecting performances to competitions
        performances = PerformanceParser(
            session.tables["schedule"].column_mapping
        ).parse(schedule_df)
        for performance, competition_id in performances:
            competition = graph.get_competition_by_id(competition_id)
            if competition:
                competition.performances.append(performance)
                performance.competition = competition
            else:
                print(f"Competition with id {competition_id} not found for performance in row {performance}")
            graph.performances.append(performance)

        # Connecting judges to competitions
        juries = JuryParser(session.tables["jury"].column_mapping).parse(jury_df)
        for jury, assignments in juries:
            for competition_id in assignments:
                competition = graph.get_competition_by_id(competition_id)
                if competition:
                    competition.juries.append(jury)
                else:
                    print(f"Competition with id {competition_id} not found for jury assignment of {jury.name}")
                    continue
                for performance in competition.performances:
                    jury.performances.append(performance)
            graph.juries.append(jury)

        # Connecting competitors to competitions
        dancers = CompetitorsParser(
            session.tables["competitors"].column_mapping
        ).parse(competitors_df)
        for pairs in dancers:
            dancer = pairs[0]
            competitions = pairs[1]
            for competition_id in competitions:
                competition = graph.get_competition_by_id(competition_id)
                if competition:
                    competition.competitors.append(dancer)
                else:
                    print(f"Competition with id {competition_id} not found for competitor registration of {dancer.full_name_1}")
                for performance in competition.performances:
                    dancer.performances.append(performance)
            graph.competitors.append(dancer)

        return graph
