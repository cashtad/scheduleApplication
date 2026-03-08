from core import AppSession
from graph import ScheduleGraph
from parsers import CompetitionParser, CompetitorsParser, JuryParser, PerformanceParser


class GraphBuilder:
    """Builds ScheduleGraph from AppSession.
    Does NOT read files — uses already-loaded DataFrames from session."""

    @staticmethod
    def build(session: AppSession) -> ScheduleGraph:
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

        # Parse competitions
        competitions_df = get_df("competitions")
        competitions = CompetitionParser(
            session.tables["competitions"].column_mapping
        ).parse(competitions_df)
        graph.set_competitions(competitions)

        # Connecting performances to competitions
        schedule_df = get_df("schedule")
        performances = PerformanceParser(
            session.tables["schedule"].column_mapping
        ).parse(schedule_df)
        graph.set_performances(performances)

        # Connecting judges to competitions
        jury_df = get_df("jury")
        juries = JuryParser(session.tables["jury"].column_mapping).parse(jury_df)
        graph.set_juries(juries)

        # Connecting competitors to competitions
        competitors_df = get_df("competitors")
        competitors = CompetitorsParser(
            session.tables["competitors"].column_mapping
        ).parse(competitors_df)
        graph.set_competitors(competitors)

        return graph
