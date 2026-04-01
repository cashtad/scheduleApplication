from __future__ import annotations

from ..dto import (
    AnalyzeReadinessResult,
    ReadinessDecision,
    ReadinessReason, ReadinessReasonSeverity, PrepareDataResult
)
from src.domain import ScheduleRepositoryValidationReport
from .analyze_readiness_policy import AnalyzeReadinessPolicy


class DefaultAnalyzeReadinessPolicy(AnalyzeReadinessPolicy):
    def __init__(self, row_error_threshold: float = 0.5) -> None:
        self._row_error_threshold = row_error_threshold

    @property
    def row_error_threshold(self) -> float:
        return self._row_error_threshold

    def evaluate(
        self,
        prepare_data_result: PrepareDataResult,
        repository_validation_report: ScheduleRepositoryValidationReport,
    ) -> AnalyzeReadinessResult:
        reasons: list[ReadinessReason] = []

        #TODO: rewrite to use more flexible approach with rules and conditions instead of hardcoded blocks

        # BLOCK 1: schema errors
        # if prepare_data_result.schema_errors_count > 0:
        #     reasons.append(
        #         ReadinessReason(
        #             code="SCHEMA_ERRORS_PRESENT",
        #             severity=ReadinessReasonSeverity.ERROR,
        #             message_en="Schema validation errors are present.",
        #             message_cz="Byly nalezeny chyby struktury tabulek.",
        #             context={"schema_errors_count": prepare_data_result.schema_errors_count},
        #         )
        #     )

        # BLOCK 2: row error threshold exceeded
        # if prepare_data_result.row_error_rate > self._row_error_threshold:
        #     reasons.append(
        #         ReadinessReason(
        #             code="ROW_ERROR_RATE_EXCEEDED",
        #             severity=ReadinessReasonSeverity.ERROR,
        #             message_en="Row error rate exceeded allowed threshold.",
        #             message_cz="Podíl chyb v řádcích překročil povolený limit.",
        #             context={
        #                 "row_error_rate": prepare_data_result.row_error_rate,
        #                 "threshold": self._row_error_threshold,
        #             },
        #         )
        #     )

        # BLOCK 3: repository validation errors
        # if repository_validation_report.errors:
        #     reasons.append(
        #         ReadinessReason(
        #             code="REPOSITORY_ERRORS_PRESENT",
        #             severity=ReadinessReasonSeverity.ERROR,
        #             message_en="Repository validation errors are present.",
        #             message_cz="Byly nalezeny chyby konzistence dat po sestavení repozitáře.",
        #             context={"repository_errors_count": len(repository_validation_report.errors)},
        #         )
        #     )

        # check for not parsed tables
        if not prepare_data_result.jury_members:
            reasons.append(
                ReadinessReason(
                    code="JURY_MEMBERS_WERE_NOT_PARSED",
                    severity=ReadinessReasonSeverity.ERROR,
                    message_en="Jury members were not parsed.",
                    message_cz="Tabulka s členy poroty nebyla úspěšně načtena. Zkontrolujte, zda je správně zvolena a namapována.",
                    context={"jury_members_count": len(prepare_data_result.jury_members)},
                )
            )

        if not prepare_data_result.competitions:
            reasons.append(
                ReadinessReason(
                    code="COMPETITIONS_WERE_NOT_PARSED",
                    severity=ReadinessReasonSeverity.ERROR,
                    message_en="Competitions were not parsed.",
                    message_cz="Tabulka s informacemi o soutěžích nebyla úspěšně načtena. Zkontrolujte, zda je správně zvolena a namapována.",
                    context={"competitions_count": len(prepare_data_result.competitions)},
                )
            )

        if not prepare_data_result.performances:
            reasons.append(
                ReadinessReason(
                    code="PERFORMANCES_WERE_NOT_PARSED",
                    severity=ReadinessReasonSeverity.ERROR,
                    message_en="Performances were not parsed.",
                    message_cz="Tabulka s harmonogramem nebyla úspěšně načtena. Zkontrolujte, zda je správně zvolena a namapována.",
                    context={"performances_count": len(prepare_data_result.performances)},
                )
            )

        if not prepare_data_result.competitors:
            reasons.append(
                ReadinessReason(
                    code="COMPETITORS_WERE_NOT_PARSED",
                    severity=ReadinessReasonSeverity.ERROR,
                    message_en="Competitors were not parsed.",
                    message_cz="Tabulka s informacemi o soutěžících nebyla úspěšně načtena. Zkontrolujte, zda je správně zvolena a namapována.",
                    context={"competitors_count": len(prepare_data_result.competitors)},
                )
            )

        # NON-BLOCK: warnings
        warnings_count = prepare_data_result.total_warnings_count + len(repository_validation_report.warnings)
        if warnings_count > 0:
            reasons.append(
                ReadinessReason(
                    code="WARNINGS_PRESENT",
                    severity=ReadinessReasonSeverity.WARNING,
                    message_en="Warnings are present.",
                    message_cz="Byla nalezena upozornění v datech.",
                    context={"warnings_count": warnings_count},
                )
            )

        has_blocking_error = any(r.severity == ReadinessReasonSeverity.ERROR for r in reasons)
        decision = ReadinessDecision.BLOCK if has_blocking_error else ReadinessDecision.ALLOW
        return AnalyzeReadinessResult(decision=decision, reasons=reasons)