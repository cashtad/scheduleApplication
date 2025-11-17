import networkx as nx
import matplotlib.pyplot as plt

from src.graph.graph import ScheduleGraph


class ScheduleGraphVisualizer:
    def __init__(self, schedule_graph: ScheduleGraph):
        self.schedule_graph = schedule_graph

    def build_graph(self):
        G = nx.Graph()

        # --- Add nodes ---
        for competition in self.schedule_graph.competitions:
            G.add_node(
                f"CMP-{competition.id}",
                label=competition.name,
                type="competition"
            )

        for jury in self.schedule_graph.juries:
            G.add_node(
                f"JURY-{jury.name}",
                label=jury.name,
                type="jury"
            )

        for competitor in self.schedule_graph.competitors:
            G.add_node(
                f"COMP-{competitor.full_name_1}",
                label=competitor.full_name_1,
                type="competitor"
            )

        for performance in self.schedule_graph.performances:
            G.add_node(
                f"PERF-{performance.competition.name}",
                label=f"Perf {performance.competition.name}",
                type="performance"
            )

        # --- Add edges (relations) ---

        # Competition ↔ Performances
        for competition in self.schedule_graph.competitions:
            for perf in competition.performances:
                G.add_edge(f"CMP-{competition.id}", f"PERF-{perf.competition.name}")

        # Competition ↔ Juries
        for competition in self.schedule_graph.competitions:
            for jury in competition.juries:
                G.add_edge(f"CMP-{competition.id}", f"JURY-{jury.name}")

        # Competition ↔ Competitors
        for competition in self.schedule_graph.competitions:
            for competitor in competition.competitors:
                G.add_edge(
                    f"CMP-{competition.id}",
                    f"COMP-{competitor.full_name_1}"
                )

        # Competitor ↔ Performances
        for competitor in self.schedule_graph.competitors:
            for perf in competitor.performances:
                G.add_edge(
                    f"COMP-{competitor.full_name_1}",
                    f"PERF-{perf.competition.name}"
                )

        return G

    def visualize(self):
        G = self.build_graph()

        # Layout for nodes
        pos = nx.kamada_kawai_layout(G)


        # Choose colors by node types
        colors = []
        for node in G.nodes(data=True):
            t = node[1].get("type", "unknown")
            if t == "competition":
                colors.append("red")
            elif t == "jury":
                colors.append("blue")
            elif t == "competitor":
                colors.append("green")
            elif t == "performance":
                colors.append("orange")
            else:
                print(f"Unknown node type: {node, t}")
                colors.append("gray")

        # Draw
        plt.figure(figsize=(16, 10))
        nx.draw(
            G, pos,
            with_labels=True,
            labels=nx.get_node_attributes(G, "label"),
            node_color=colors,
            node_size=800,
            font_size=8,
            edge_color="gray"
        )

        plt.title("Schedule Graph Visualization")
        plt.show()
