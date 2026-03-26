from __future__ import annotations

from ..dto.build_repository_result import BuildRepositoryResult
from ..dto.prepare_data_result import PrepareDataResult
from ...domain.schedule_repository import ScheduleRepositoryBuilder


class BuildRepositoryUseCase:
    """
    Builds ScheduleRepository from parsed entities and performs repository validation.
    """

    def __init__(self, repository_builder: ScheduleRepositoryBuilder) -> None:
        self._repository_builder = repository_builder

    def execute(self, prepare_data_result: PrepareDataResult) -> BuildRepositoryResult:
        result = self._repository_builder.build(
            competitions=prepare_data_result.competitions,
            competitors=prepare_data_result.competitors,
            jury_members=prepare_data_result.jury_members,
            performances=prepare_data_result.performances,
        )
        return BuildRepositoryResult( # TODO mb fix two duplicate dataclasses. result already contains repository and report
            repository=result.repository,
            validation_report=result.validation_report,
        )