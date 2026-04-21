from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass, field
from typing import Any

from src.domain.analysis import ScheduleAnalysisResult, Violation


@dataclass(frozen=True, slots=True)
class LocalizedDetailItem:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class ViolationViewItem:
    violation_id: str
    rule_name: str
    rule_display_name: str
    severity: str
    description: str
    entity_name: str
    source_rows: list[int]
    details: dict[str, Any]
    localized_details: list[LocalizedDetailItem] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AnalysisViewModel:
    summary: dict
    violations: list[ViolationViewItem] = field(default_factory=list)
    row_to_violation_ids: dict[int, list[str]] = field(default_factory=dict)
    violation_id_to_rows: dict[str, list[int]] = field(default_factory=dict)


class AnalysisViewPresenter:
    _RULE_NAMES_CS = {
        "MaxContinuousDancing": "Nepřetržitý čas tance",
        "CostumeChangeTime": "Čas na převlečení kostýmu",
        "MaxContinuousJudging": "Nepřetržitý čas rozhodování",
        "MaxGapBetweenPerformances": "Velká přestávka mezi vystoupeními",
        "SimultaneousDancing": "Současné taneční vystoupení",
        "SimultaneousJudging": "Současné rozhodování",
    }

    # Internal tuning/config fields are intentionally hidden from end users.
    _HIDDEN_KEYS = {
        "threshold_minutes",
        "required_minutes",
        "excess_minutes",
        "shortage_minutes",
    }

    def build(self, result: ScheduleAnalysisResult) -> AnalysisViewModel:
        violation_items: list[ViolationViewItem] = []
        row_to_violation_ids: dict[int, list[str]] = {}
        violation_id_to_rows: dict[str, list[int]] = {}

        for idx, violation in enumerate(result.violations):
            violation_id = _make_violation_id(violation, idx)
            rows = sorted(set(violation.source_rows))

            violation_items.append(
                ViolationViewItem(
                    violation_id=violation_id,
                    rule_name=violation.rule_name,
                    rule_display_name=self._RULE_NAMES_CS.get(
                        violation.rule_name, violation.rule_name
                    ),
                    severity=violation.severity.value,
                    description=violation.description,
                    entity_name=violation.entity_name,
                    source_rows=rows,
                    details=dict(violation.details),
                    localized_details=self._format_details(violation),
                )
            )

            violation_id_to_rows[violation_id] = rows
            for row in rows:
                row_to_violation_ids.setdefault(row, []).append(violation_id)

        return AnalysisViewModel(
            summary=result.get_summary(),
            violations=violation_items,
            row_to_violation_ids=row_to_violation_ids,
            violation_id_to_rows=violation_id_to_rows,
        )

    def _format_details(self, violation: Violation) -> list[LocalizedDetailItem]:
        details = violation.details
        rule_name = violation.rule_name
        items: list[LocalizedDetailItem] = []

        def add(label: str, value: Any) -> None:
            text = self._format_value(value)
            if text:
                items.append(LocalizedDetailItem(label=label, value=text))

        if rule_name == "MaxGapBetweenPerformances":
            add("Přestavka", self.format_minutes_into_hours(details.get("gap_minutes")))
            add("Časový úsek", self._format_time_range(details, "from_time", "to_time"))
        elif rule_name == "CostumeChangeTime":
            add("Dostupný čas na převlečení", self.format_minutes_into_hours(details.get("gap_minutes")))
            add(
                "Přechod disciplín",
                self._format_pair(details, "from_discipline", "to_discipline", " -> "),
            )
            add("Časový úsek", self._format_time_range(details, "from_time", "to_time"))
        elif rule_name in {"MaxContinuousDancing", "MaxContinuousJudging"}:
            add("Délka souvislé aktivity", self.format_minutes_into_hours(details.get("duration_minutes")))
            add(
                "Časový úsek",
                self._format_time_range(details, "start_time", "end_time"),
            )
        elif rule_name in {"SimultaneousDancing", "SimultaneousJudging"}:
            add("Doba překryvu", self.format_minutes_into_hours(details.get("overlap_minutes")))
            add(
                "Čas překryvu",
                self._format_time_range(details, "overlap_start", "overlap_end"),
            )
            add(
                "Soutěže",
                self._format_pair(details, "competition1", "competition2", " <-> "),
            )

        known_labels = {item.label for item in items}
        if not known_labels:
            for key, value in details.items():
                if key in self._HIDDEN_KEYS:
                    continue
                label = self._humanize_key(key)
                add(label, value)

        return items

    def format_minutes_into_hours(self, minutes: Any) -> str:
        if minutes is None or not isinstance(minutes, (int, float)):
            return ""
        if isinstance(minutes, float):
            minutes = int(minutes)
        hours, minutes = self.minutes_to_hours_minutes(minutes)
        if hours > 0:
            return f"{int(hours)} h {int(minutes)} min" if minutes > 0 else f"{int(hours)}h"
        else:
            return f"{int(minutes)} min"

    def minutes_to_hours_minutes(self, minutes: int) -> tuple[int, int]:
        hours = minutes // 60
        minutes = minutes % 60
        return hours, minutes

    def _format_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%H:%M")
        if isinstance(value, float):
            return f"{value:.0f} min"
        if isinstance(value, int):
            return f"{value} min"
        return str(value)

    def _format_time_range(
        self,
        details: dict[str, Any],
        start_key: str,
        end_key: str,
    ) -> str:
        start = details.get(start_key)
        end = details.get(end_key)
        if start is None or end is None:
            return ""
        return f"{self._format_clock(start)} - {self._format_clock(end)}"

    def _format_pair(
        self,
        details: dict[str, Any],
        left_key: str,
        right_key: str,
        separator: str,
    ) -> str:
        left = details.get(left_key)
        right = details.get(right_key)
        if left is None or right is None:
            return ""
        return f"{left}{separator}{right}"

    @staticmethod
    def _format_clock(value: Any) -> str:
        if isinstance(value, datetime):
            return value.strftime("%H:%M")
        return str(value)

    @staticmethod
    def _humanize_key(key: str) -> str:
        text = key.replace("_", " ").strip()
        return text[:1].upper() + text[1:] if text else key


def build_analysis_view_model(result: ScheduleAnalysisResult) -> AnalysisViewModel:
    return AnalysisViewPresenter().build(result)


def _make_violation_id(v: Violation, index: int) -> str:
    base = f"{v.rule_name}|{v.entity_id}|{v.severity.value}|{index}"
    return base
