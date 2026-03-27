from __future__ import annotations

from datetime import datetime

from ..dto.analyze_workflow_result import AnalyzeWorkflowResult
from ..dto.data_quality_report import DataQualityReport
from ..dto.prepare_data_result import PrepareDataResult
from ..dto.readiness import AnalyzeReadinessResult, ReadinessDecision, ReadinessReason
from ..dto.workflow_status import WorkflowStatus
from ..policies.analyze_readiness_policy import AnalyzeReadinessPolicy
from ..use_cases.build_repository_use_case import BuildRepositoryUseCase
from ..use_cases.prepare_data_use_case import PrepareDataUseCase
from ..use_cases.run_schedule_analysis_use_case import RunScheduleAnalysisUseCase
from ...domain.schedule_repository import ScheduleRepositoryValidationReport


class AnalyzeWorkflowService:
    def __init__(
        self,
        prepare_data_use_case: PrepareDataUseCase,
        build_repository_use_case: BuildRepositoryUseCase,
        run_schedule_analysis_use_case: RunScheduleAnalysisUseCase,
        readiness_policy: AnalyzeReadinessPolicy,
        row_error_threshold: float = 0.5,
    ) -> None:
        self._prepare_data_use_case = prepare_data_use_case
        self._build_repository_use_case = build_repository_use_case
        self._run_schedule_analysis_use_case = run_schedule_analysis_use_case
        self._readiness_policy = readiness_policy
        self._row_error_threshold = row_error_threshold

    def run_analysis(self, session) -> AnalyzeWorkflowResult:
        try:
            prepared = self._prepare_data_use_case.execute(session)

            # Build repository always: gives additional consistency diagnostics
            built = self._build_repository_use_case.execute(prepared)

            readiness = self._readiness_policy.evaluate(
                prepare_data_result=prepared,
                repository_validation_report=built.validation_report,
            )

            quality_report = DataQualityReport(
                generated_at=datetime.now(),
                row_error_threshold=self._row_error_threshold,
                prepare_data_result=prepared,
                repository_validation_report=built.validation_report,
                readiness_result=readiness,
            )

            if not readiness.is_allowed:
                return AnalyzeWorkflowResult(
                    status=WorkflowStatus.BLOCKED,
                    quality_report=quality_report,
                )

            analysis = self._run_schedule_analysis_use_case.execute(built)
            return AnalyzeWorkflowResult(
                status=WorkflowStatus.SUCCESS,
                quality_report=quality_report,
                analysis_result=analysis.analysis_result,
                html_report_path=analysis.html_report_path,
            )

        except Exception as exc:
            return AnalyzeWorkflowResult(
                status=WorkflowStatus.FAILED,
                quality_report=self._build_fallback_quality_report(str(exc)),
                error_message=str(exc),
            )

    def _build_fallback_quality_report(self, error_message: str) -> DataQualityReport:
        fallback_prepared = PrepareDataResult()
        fallback_repo_report = ScheduleRepositoryValidationReport(errors=[], warnings=[])
        fallback_readiness = AnalyzeReadinessResult(
            decision=ReadinessDecision.BLOCK,
            reasons=[
                ReadinessReason(
                    code="WORKFLOW_EXCEPTION",
                    severity="error",
                    message_en=error_message,
                    message_cz="Došlo k neočekávané chybě během zpracování.",
                )
            ],
        )
        return DataQualityReport(
            generated_at=datetime.now(),
            row_error_threshold=self._row_error_threshold,
            prepare_data_result=fallback_prepared,
            repository_validation_report=fallback_repo_report,
            readiness_result=fallback_readiness,
        )