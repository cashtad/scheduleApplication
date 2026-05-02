from __future__ import annotations

from ..schedule_repository import ScheduleRepository
from ..schedule_repository_validation import (
	ScheduleRepositoryValidationIssue,
	ValidationIssueSeverity,
)


def check_competitions_not_used(
	repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
	issues: list[ScheduleRepositoryValidationIssue] = []

	for competition in repository.competitions_by_id.values():
		if repository.list_performances_by_competition_id(competition.id):
			continue

		issues.append(
			ScheduleRepositoryValidationIssue(
				code="COMPETITION_WITHOUT_PERFORMANCES",
				message=f"Soutěž '{competition.name}' (ID: {competition.id}) nemá žádná vystoupení",
				severity=ValidationIssueSeverity.WARNING,
				context={"competition_id": competition.id},
			)
		)

	return issues


def check_competitions_not_empty(
	repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
	if repository.competitions_by_id:
		return []

	return [
		ScheduleRepositoryValidationIssue(
			code="NO_COMPETITIONS_PARSED",
			message="Nenalezena žádná soutěž. Zkontrolujte, zda je správně zvolena a namapována tabulka s informacemi o soutěžích.",
			severity=ValidationIssueSeverity.ERROR,
			context={},
		)
	]


def check_competitors_not_empty(
	repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
	if repository.competitors:
		return []

	return [
		ScheduleRepositoryValidationIssue(
			code="NO_COMPETITORS_PARSED",
			message="Nenalezen žádný soutěžící. Zkontrolujte, zda je správně zvolena a namapována tabulka s informacemi o soutěžících.",
			severity=ValidationIssueSeverity.ERROR,
			context={},
		)
	]


def check_jury_members_not_empty(
	repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
	if repository.jury_members:
		return []

	return [
		ScheduleRepositoryValidationIssue(
			code="NO_JURY_MEMBERS_PARSED",
			message="Nenalezen žádný člen poroty. Zkontrolujte, zda je správně zvolena a namapována tabulka s členy poroty. Pokud jste tabulku nenahráli, toto upozornění ignorujte",
			severity=ValidationIssueSeverity.WARNING,
			context={},
		)
	]


def check_performances_not_empty(
	repository: ScheduleRepository,
) -> list[ScheduleRepositoryValidationIssue]:
	if repository.performances_by_competition_id:
		return []

	return [
		ScheduleRepositoryValidationIssue(
			code="NO_PERFORMANCES_PARSED",
			message="Nenalezena žádná vystoupení. Zkontrolujte, zda je správně zvolena a namapována tabulka s harmonogramem.",
			severity=ValidationIssueSeverity.ERROR,
			context={},
		)
	]



