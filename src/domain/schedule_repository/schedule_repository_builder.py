from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..model import Competition, Competitor, JuryMember, Performance
from .schedule_repository import ScheduleRepository
from .schedule_repository_validation import ScheduleRepositoryValidationReport
from .schedule_repository_validator import ScheduleRepositoryValidator


@dataclass(frozen=True, slots=True)
class BuildScheduleRepositoryResult:
    repository: ScheduleRepository
    validation_report: ScheduleRepositoryValidationReport


class ScheduleRepositoryBuilder:
    @staticmethod
    def build(
        competitions: Iterable[Competition],
        competitors: Iterable[Competitor],
        jury_members: Iterable[JuryMember],
        performances: Iterable[Performance],
    ) -> BuildScheduleRepositoryResult:
        repository = ScheduleRepository()

        for competition in competitions:
            repository.add_competition(competition)

        for competitor in competitors:
            repository.add_competitor(competitor)

        for jury_member in jury_members:
            repository.add_jury_member(jury_member)

        for performance in performances:
            repository.add_performance(performance)

        validation_report = ScheduleRepositoryValidator.validate(repository)
        return BuildScheduleRepositoryResult(
            repository=repository,
            validation_report=validation_report,
        )