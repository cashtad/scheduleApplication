from pathlib import Path

from src.graph.graph import ScheduleGraph

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent  # /src
    CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

    graph = ScheduleGraph()
    graph.fill_with_data(str(CONFIG_PATH))

    competitors = graph.get_competitors()

    for competitor in competitors:
        print("\n\n\nCompetitor:", competitor.full_name_1)
        results = graph.get_performances_by_fullname(competitor.full_name_1)
        for result in results:
            print(result)

