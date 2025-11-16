from src.graph.graph import ScheduleGraph



if __name__ == "__main__":
    graph = ScheduleGraph()
    graph.fill_with_data("C://Users/Leonid/PycharmProjects/scheduleApplication/src/config/config.yaml")

    print("All performances of Viktorie Šerá:")

    result = graph.get_performances_by_fullname("Viktorie Šerá")

    for performance in result:
        print(performance)

