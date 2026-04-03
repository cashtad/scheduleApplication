from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.application.policies import DefaultAnalyzeReadinessPolicy
from src.application.services import (
    SessionRuntimeDataSyncService,
    SessionStatusSyncService,
)
from src.application.use_cases import (
    BuildRepositoryUseCase,
    PrepareDataUseCase,
    RestoreSessionUseCase,
    RunScheduleAnalysisUseCase,
    SaveSessionUseCase,
    RevalidateSessionUseCase,
)
from src.application.workflow import AnalyzeWorkflowService
from src.domain import ScheduleRepositoryBuilder, InferenceEngine
from src.ingestion import TableIngestionService
from src.infrastructure import (
    JsonSessionStore,
    PandasExcelReader,
    HtmlExplanationReportWriter,
    YamlRulesConfigLoader,
)


@dataclass(frozen=True, slots=True)
class AppContainer:
    analyze_workflow_service: AnalyzeWorkflowService
    restore_session_use_case: RestoreSessionUseCase
    save_session_use_case: SaveSessionUseCase
    revalidate_session_use_case: RevalidateSessionUseCase


def build_app_container(
    rules_config_path: str | Path,
    *,
    row_error_threshold: float = 0.5,
    reports_dir: str = ".reports",
    with_html_report_writer: bool = True,
    session_store: JsonSessionStore | None = None,
    excel_reader: PandasExcelReader | None = None,
) -> AppContainer:
    store = session_store or JsonSessionStore()
    reader = excel_reader or PandasExcelReader()

    rules_config = YamlRulesConfigLoader.load_from_file(rules_config_path)

    repository_builder = ScheduleRepositoryBuilder()
    inference_engine = InferenceEngine(rules_config=rules_config)

    save_session_use_case = SaveSessionUseCase(store)
    restore_session_use_case = RestoreSessionUseCase(store)

    ingestion_service = TableIngestionService(excel_reader=reader)
    status_sync_service = SessionStatusSyncService()
    runtime_data_sync_service = SessionRuntimeDataSyncService()

    prepare_data_use_case = PrepareDataUseCase(
        table_ingestion_service=ingestion_service,
        session_status_sync_service=status_sync_service,
        session_runtime_data_sync_service=runtime_data_sync_service,
    )
    build_repository_use_case = BuildRepositoryUseCase(
        repository_builder=repository_builder
    )

    html_writer = (
        HtmlExplanationReportWriter(output_dir=reports_dir)
        if with_html_report_writer
        else None
    )
    run_schedule_analysis_use_case = RunScheduleAnalysisUseCase(
        inference_engine=inference_engine,
        html_report_writer=html_writer,
    )

    readiness_policy = DefaultAnalyzeReadinessPolicy(
        row_error_threshold=row_error_threshold
    )

    analyze_workflow_service = AnalyzeWorkflowService(
        prepare_data_use_case=prepare_data_use_case,
        build_repository_use_case=build_repository_use_case,
        run_schedule_analysis_use_case=run_schedule_analysis_use_case,
        readiness_policy=readiness_policy,
        row_error_threshold=row_error_threshold,
    )

    revalidate_session_use_case = RevalidateSessionUseCase(
        table_ingestion_service=ingestion_service,
        session_status_sync_service=status_sync_service,
        save_session_use_case=save_session_use_case,
    )

    return AppContainer(
        analyze_workflow_service=analyze_workflow_service,
        restore_session_use_case=restore_session_use_case,
        save_session_use_case=save_session_use_case,
        revalidate_session_use_case=revalidate_session_use_case,
    )
