from pathlib import Path

from src.graph.graph import ScheduleGraph
from src.expert_system.inference_engine import InferenceEngine
from src.expert_system.explanation import ExplanationGenerator

if __name__ == "__main__":
    # Define paths to configuration files
    BASE_DIR = Path(__file__).parent  # /src
    CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
    RULES_CONFIG_PATH = BASE_DIR / "config" / "rules_config.yaml"

    # Load schedule graph from data
    print("📥 Načítání rozvrhu...")
    graph = ScheduleGraph()
    graph.fill_with_data(str(CONFIG_PATH))

    # Initialize expert system with rules
    print("🔧 Inicializace expertního systému...")
    inference_engine = InferenceEngine(str(RULES_CONFIG_PATH))

    # Analyze schedule for rule violations
    print("🔍 Analýza rozvrhu...\n")
    result = inference_engine.analyze_schedule(graph)

    # Generate reports
    explanation_gen = ExplanationGenerator()
    #
    # # Console report
    # console_report = explanation_gen.generate_console_report(result)
    # print(console_report)
    #
    # # Additional demonstration: violations by participants
    # print("\n" + "=" * 80)
    # print("DETAILNÍ INFORMACE O PORUŠENÍCH PODLE ÚČASTNÍKŮ")
    # print("=" * 80 + "\n")
    #
    # # Group violations by entity (dancer/judge)
    # violations_by_entity = {}
    # for violation in result.violations:
    #     entity_name = violation.entity_name
    #     if entity_name not in violations_by_entity:
    #         violations_by_entity[entity_name] = []
    #     violations_by_entity[entity_name].append(violation)
    #
    # # Sort by total weight (most problematic first)
    # for entity_name, violations in sorted(
    #     violations_by_entity.items(),
    #     key=lambda x: sum(v.weight for v in x[1]),
    #     reverse=True
    # ):
    #     total_weight = sum(v.weight for v in violations)
    #     print(f"👤 {entity_name}: {len(violations)} porušení (váha: {total_weight:.1f})")
    #     sorted_violations = sorted(violations, key=lambda v: -v.weight)
    #     for v in sorted_violations:
    #         icon = explanation_gen.SEVERITY_COLORS[v.severity]
    #         print(f"   {icon} {v.rule_name}: {v.description}")
    #     print()

    # HTML report
    output_html = BASE_DIR.parent / "schedule_analysis_report.html"
    explanation_gen.generate_html_report(result, str(output_html))
    print(f"\n💾 HTML zpráva uložena: {output_html}")

    results = graph.get_performances_by_fullname("Eva Chovancová")
    for result in results:
        print(result)


