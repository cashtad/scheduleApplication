from src.graph.graph import ScheduleGraph
from src.graph.graph_visualizer import ScheduleGraphVisualizer

if __name__ == "__main__":
    graph = ScheduleGraph()
    graph.fill_with_data("C://Users/Leonid/PycharmProjects/scheduleApplication/src/config/config.yaml")

    visualizer = ScheduleGraphVisualizer(graph)
    visualizer.visualize()

