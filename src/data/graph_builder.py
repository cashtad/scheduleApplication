from core import AppSession, GraphBuildStats, AnalysisError
from graph import ScheduleGraph
from parsers import CompetitionParser, CompetitorsParser, JuryParser, PerformanceParser


class GraphBuilder:
    @staticmethod
    def build(session: AppSession) -> tuple[ScheduleGraph, GraphBuildStats]:
        try:
            graph = ScheduleGraph()
            stats = GraphBuildStats()

            def get_df(key):
                ts = session.tables[key]
                df = ts.raw_df
                if ts.selected_rows is not None:
                    df = df.loc[ts.selected_rows]
                return df

            competitions, stats.competitions = CompetitionParser(
                session.tables["competitions"].column_mapping
            ).parse(get_df("competitions"))
            graph.set_competitions(competitions)

            performances, stats.performances = PerformanceParser(
                session.tables["schedule"].column_mapping
            ).parse(get_df("schedule"))
            graph.set_performances(performances)

            juries, stats.jury = JuryParser(
                session.tables["jury"].column_mapping
            ).parse(get_df("jury"))
            graph.set_juries(juries)

            competitors, stats.competitors = CompetitorsParser(
                session.tables["competitors"].column_mapping
            ).parse(get_df("competitors"))
            graph.set_competitors(competitors)

            return graph, stats
        except Exception as exc:
            raise AnalysisError(
                code="GRAPH_BUILD_FAILED",
                user_message="Nepodařilo se sestavit datový graf pro analýzu.",
                technical_message=str(exc),
            ) from exc