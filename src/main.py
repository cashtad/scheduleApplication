from pathlib import Path
import yaml

from src.core.session import AppSession, TableSession
from src.data.excel_loader import ExcelTableLoader
from src.data.graph_builder import GraphBuilder
from src.data.template_store import TemplateStore
from src.config.config_loader import ConfigLoader
from src.expert_system.inference_engine import InferenceEngine
from src.expert_system.explanation import ExplanationGenerator

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    RULES_CONFIG_PATH = BASE_DIR / "config" / "rules_config.yaml"
    CONFIG_PATH = BASE_DIR / "config" / "config.yaml"

    # Load rules config once
    with open(RULES_CONFIG_PATH, encoding="utf-8") as f:
        rules_config = yaml.safe_load(f)

    # Bootstrap session from legacy config.yaml (temporary until UI)
    print("📥 Načítání rozvrhu...")
    cfg = ConfigLoader(str(CONFIG_PATH)).load()

    store = TemplateStore()
    tables = {}
    for key in ["competitions", "competitors", "jury", "schedule"]:
        file_cfg = cfg.files[key]
        file_path = file_cfg["path"]
        sheet_name = file_cfg.get("sheet")
        raw_df = ExcelTableLoader(path=file_path, sheet=sheet_name).load()
        mapping = cfg.columns[key]
        # Try auto-apply from template store, fall back to config.yaml mapping
        auto_mapping = store.try_auto_apply(key, list(raw_df.columns))
        column_mapping = auto_mapping if auto_mapping is not None else mapping
        tables[key] = TableSession(
            table_key=key,
            file_path=str(file_path),
            sheet_name=sheet_name,
            raw_df=raw_df,
            column_mapping=column_mapping,
        )

    session = AppSession(tables=tables)

    # Build graph
    graph = GraphBuilder().build(session)
    session.graph = graph

    # Initialize expert system with rules
    print("🔧 Inicializace expertního systému...")
    inference_engine = InferenceEngine(rules_config)

    # Analyze schedule for rule violations
    print("🔍 Analýza rozvrhu...\n")
    result = inference_engine.analyze_schedule(graph)
    session.last_result = result

    # Generate HTML report
    explanation_gen = ExplanationGenerator()
    output_html = BASE_DIR.parent / "schedule_analysis_report.html"
    explanation_gen.generate_html_report(result, str(output_html))
    print(f"\n💾 HTML zpráva uložena: {output_html}")

    results = graph.get_performances_by_fullname("Eva Chovancová")
    for r in results:
        print(r)

