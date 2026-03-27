from __future__ import annotations

from ..dto import BuildRepositoryResult, PrepareDataResult
from ...domain import ScheduleRepositoryBuilder


class BuildRepositoryUseCase:
    def __init__(self, repository_builder: ScheduleRepositoryBuilder) -> None:
        self._repository_builder = repository_builder

    def execute(self, prepare_data_result: PrepareDataResult) -> BuildRepositoryResult:
        built = self._repository_builder.build(
            competitions=prepare_data_result.competitions,
            competitors=prepare_data_result.competitors,
            jury_members=prepare_data_result.jury_members,
            performances=prepare_data_result.performances,
        )
        return BuildRepositoryResult(
            repository=built.repository,
            validation_report=built.validation_report,
        )