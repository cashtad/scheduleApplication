from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Dict


# matches:
# "1"      -> prefix=""  number=1
# "#1"     -> prefix="#" number=1
# "comp12" -> prefix="comp" number=12
_PREFIX_RE = re.compile(r"^(?P<prefix>.*?)(?P<number>\d+)$")

@dataclass(slots=True, frozen=True)
class PrefixCandidate:
    prefix: str
    columns: List[str]
    numbers: List[int]

    @property
    def size(self) -> int:
        return len(self.columns)


@dataclass(slots=True, frozen=True)
class PrefixDetectionResult:
    candidates: List[PrefixCandidate]
    best_prefix: str | None

    # ---------- helpers for UI ----------

    def find_by_prefix(self, prefix: str) -> PrefixCandidate | None:
        for c in self.candidates:
            if c.prefix == prefix:
                return c
        return None

    def columns_for_prefix(self, prefix: str) -> List[str]:
        candidate = self.find_by_prefix(prefix)
        return candidate.columns if candidate else []

    def count_for_prefix(self, prefix: str) -> int:
        candidate = self.find_by_prefix(prefix)
        return candidate.size if candidate else 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_prefixes(columns: Iterable[str]) -> PrefixDetectionResult:
    parsed_columns = [str(c).strip() for c in columns]

    # prefix -> numbers + columns
    groups: Dict[str, List[tuple[str, int]]] = {}

    for col in parsed_columns:
        match = _PREFIX_RE.match(col)
        if not match:
            continue

        prefix = match.group("prefix")
        number = int(match.group("number"))

        groups.setdefault(prefix, []).append((col, number))

    candidates: List[PrefixCandidate] = []

    for prefix, items in groups.items():
        # ignore tiny groups (almost always noise)
        if len(items) < 2:
            continue

        columns_sorted = [col for col, _ in sorted(items, key=lambda x: x[1])]
        numbers_sorted = sorted(num for _, num in items)

        candidates.append(
            PrefixCandidate(
                prefix=prefix,
                columns=columns_sorted,
                numbers=numbers_sorted,
            )
        )

    # Sort by size descending → most likely prefix first
    candidates.sort(key=lambda c: c.size, reverse=True)

    best_prefix = candidates[0].prefix if candidates else None

    return PrefixDetectionResult(
        candidates=candidates,
        best_prefix=best_prefix,
    )