from pathlib import Path

from src.graph.graph import ScheduleGraph
from src.graph.graph_visualizer import ScheduleGraphVisualizer

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent  # /src
    CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

    graph = ScheduleGraph()
    graph.fill_with_data(str(CONFIG_PATH))

    visualizer = ScheduleGraphVisualizer(graph)
    visualizer.visualize()

