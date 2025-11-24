from src.graph.graph import ScheduleGraph

if __name__ == "__main__":
    graph = ScheduleGraph()
    graph.fill_with_data("C://Users/Leonid/PycharmProjects/scheduleApplication/src/config/config.yaml")

    competitors = graph.get_competitors()

    for competitor in competitors:
        print("\n\n\nCompetitor:", competitor.full_name_1)
        results = graph.get_performances_by_fullname(competitor.full_name_1)
        for result in results:
            print(result)

