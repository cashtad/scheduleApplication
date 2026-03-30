from __future__ import annotations

from pathlib import Path

from src.application.bootstrap import build_app_container
from src.application.dto.analysis_view import build_analysis_view_model
from src.session import AppSession


def run_once() -> None:
    container = build_app_container(
        rules_config_path=Path("rules_config.yaml"),
        reports_dir=".reports",
        with_html_report_writer=True,
    )

    session: AppSession = container.restore_session_use_case.execute()

    # NOTE:
    # At this point UI should let user select files/sheets/mappings.
    # Here we just run analysis with whatever session currently has.
    result = container.analyze_workflow_service.run_analysis(session)

    print(f"Workflow status: {result.status.value}")

    if result.status.value == "failed":
        print(f"Error: {result.error_message}")
        return

    if result.status.value == "blocked":
        print("Analysis blocked by readiness policy:")
        for reason in result.quality_report.readiness_result.reasons:
            print(f"- [{reason.severity.value}] {reason.code}: {reason.message_en}")
        return

    # SUCCESS
    assert result.analysis_result is not None
    view_model = build_analysis_view_model(result.analysis_result)

    print("Analysis summary:")
    print(view_model.summary)
    print(f"Violations count: {len(view_model.violations)}")

    if result.html_report_path:
        print(f"HTML report: {result.html_report_path}")


if __name__ == "__main__":
    run_once()