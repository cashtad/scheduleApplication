from typing import Optional

from classes import Competition, Competitor, Jury, Performance


class ScheduleGraph:
    """In-memory graph connecting all schedule entities."""

    def __init__(self):
        self.competitors:  set[Competitor]  = set()
        self.performances: set[Performance] = set()
        self.juries:       set[Jury]        = set()
        self.competitions: set[Competition] = set()

    # ------------------------------------------------------------------
    # Setters / getters
    # ------------------------------------------------------------------

    def set_competitors(self, competitors: set[Competitor]) -> None:
        self.competitors = competitors

    def set_juries(self, juries: set[Jury]) -> None:
        self.juries = juries

    def set_competitions(self, competitions: set[Competition]) -> None:
        self.competitions = competitions

    def set_performances(self, performances: set[Performance]) -> None:
        self.performances = performances

    def get_competitors(self) -> set[Competitor]:
        return self.competitors

    def get_juries(self) -> set[Jury]:
        return self.juries

    def get_competitions(self) -> set[Competition]:
        return self.competitions

    def get_performances(self) -> set[Performance]:
        return self.performances

    # ------------------------------------------------------------------
    # Lookups by identity
    # ------------------------------------------------------------------

    def get_competitor_by_fullname(self, fullname: str) -> Optional[Competitor]:
        """Return the competitor whose first or second name matches *fullname*."""
        return next(
            (c for c in self.competitors
             if c.full_name_1 == fullname or c.full_name_2 == fullname),
            None,
        )

    def get_jury_by_fullname(self, fullname: str) -> Optional[Jury]:
        """Return the jury member with the given full name."""
        return next((j for j in self.juries if j.fullname == fullname), None)

    def get_competition_by_id(self, competition_id: int) -> Optional[Competition]:
        """Return the competition with the given id."""
        return next((c for c in self.competitions if c.id == competition_id), None)

    # ------------------------------------------------------------------
    # Performance queries
    # ------------------------------------------------------------------

    def get_performances_by_competition_ids(self, competition_ids: set[int]) -> list[Performance]:
        """Return all performances whose competition_id is in *competition_ids*."""
        return [p for p in self.performances if p.competition_id in competition_ids]

    def get_performances_of_competitor(self, competitor: Competitor) -> list[Performance]:
        return self.get_performances_by_competition_ids(competitor.competition_ids)

    def get_performances_of_jury(self, jury: Jury) -> list[Performance]:
        return self.get_performances_by_competition_ids(jury.competition_ids)

    def get_performances_of_competitor_by_fullname(self, fullname: str) -> set[Performance]:
        competitor = self.get_competitor_by_fullname(fullname)
        if competitor is None:
            return set()
        return set(self.get_performances_of_competitor(competitor))

    def get_performances_of_jury_by_fullname(self, fullname: str) -> set[Performance]:
        jury = self.get_jury_by_fullname(fullname)
        if jury is None:
            return set()
        return set(self.get_performances_of_jury(jury))