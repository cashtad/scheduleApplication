from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.analysis import ScheduleAnalysisResult, Violation


@dataclass(frozen=True, slots=True)
class ViolationViewItem:
    violation_id: str
    rule_name: str
    severity: str
    description: str
    entity_name: str
    source_rows: list[int]
    details: dict


@dataclass(frozen=True, slots=True)
class AnalysisViewModel:
    summary: dict
    violations: list[ViolationViewItem] = field(default_factory=list)
    row_to_violation_ids: dict[int, list[str]] = field(default_factory=dict)
    violation_id_to_rows: dict[str, list[int]] = field(default_factory=dict)


def build_analysis_view_model(result: ScheduleAnalysisResult) -> AnalysisViewModel:
    violation_items: list[ViolationViewItem] = []
    row_to_violation_ids: dict[int, list[str]] = {}
    violation_id_to_rows: dict[str, list[int]] = {}

    for idx, v in enumerate(result.violations):
        violation_id = _make_violation_id(v, idx)
        rows = sorted(set(v.source_rows))

        violation_items.append(
            ViolationViewItem(
                violation_id=violation_id,
                rule_name=v.rule_name,
                severity=v.severity.value,
                description=v.description,
                entity_name=v.entity_name,
                source_rows=rows,
                details=v.details,
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


def _make_violation_id(v: Violation, index: int) -> str:
    base = f"{v.rule_name}|{v.entity_id}|{v.severity.value}|{index}"
    return base