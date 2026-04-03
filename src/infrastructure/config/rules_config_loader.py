from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from src.domain import Severity, RuleConfig, RulesConfig
from .default_rules_config import DEFAULT_RULES_CONFIG_YAML
from .errors import RulesConfigError


class YamlRulesConfigLoader:
    @staticmethod
    def load_from_file(file_path: str | Path) -> RulesConfig:
        path = Path(file_path)

        if not path.exists():
            YamlRulesConfigLoader._create_default_config_file(path)

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RulesConfigError(f"Nepodařilo se načíst konfiguraci pravidel: {exc}") from exc

        if not isinstance(raw, Mapping):
            raise RulesConfigError("Kořen konfigurace pravidel musí být mapování")

        return YamlRulesConfigLoader._parse(raw)

    @staticmethod
    def _create_default_config_file(path: Path) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(DEFAULT_RULES_CONFIG_YAML, encoding="utf-8")
        except Exception as exc:
            raise RulesConfigError(
                f"Soubor konfigurace pravidel nebyl nalezen a vytvoření výchozího selhalo: {path} ({exc})"
            ) from exc

    @staticmethod
    def _parse(raw: Mapping[str, Any]) -> RulesConfig:
        required = [
            "max_continuous_dancing",
            "costume_change_time",
            "max_continuous_judging",
            "max_gap_between_performances",
            "simultaneous_dancing",
            "simultaneous_judging",
        ]
        missing = [k for k in required if k not in raw]
        if missing:
            raise RulesConfigError(f"Chybějící sekce pravidel: {', '.join(missing)}")

        return RulesConfig(
            max_continuous_dancing=YamlRulesConfigLoader._parse_rule(
                raw["max_continuous_dancing"], need_thresholds=True, need_rest=True
            ),
            costume_change_time=YamlRulesConfigLoader._parse_rule(
                raw["costume_change_time"],
                need_thresholds=True,
                need_disciplines=True,
                need_min_gap=True,
            ),
            max_continuous_judging=YamlRulesConfigLoader._parse_rule(
                raw["max_continuous_judging"], need_thresholds=True, need_rest=True
            ),
            max_gap_between_performances=YamlRulesConfigLoader._parse_rule(
                raw["max_gap_between_performances"], need_thresholds=True
            ),
            simultaneous_dancing=YamlRulesConfigLoader._parse_rule(
                raw["simultaneous_dancing"], need_thresholds=False
            ),
            simultaneous_judging=YamlRulesConfigLoader._parse_rule(
                raw["simultaneous_judging"], need_thresholds=False
            ),
        )

    @staticmethod
    def _parse_rule(
        section: Any,
        *,
        need_thresholds: bool,
        need_rest: bool = False,
        need_disciplines: bool = False,
        need_min_gap: bool = False,
    ) -> RuleConfig:
        if not isinstance(section, Mapping):
            raise RulesConfigError("Sekce pravidla musí být mapování")

        enabled = bool(section.get("enabled", True))

        thresholds = None
        if need_thresholds:
            tr = section.get("thresholds")
            if not isinstance(tr, Mapping):
                raise RulesConfigError("Sekce pravidla vyžaduje mapování 'thresholds'")
            for key in ("critical", "medium", "low"):
                if key not in tr:
                    raise RulesConfigError(f"Chybí práh '{key}'")
            thresholds = {
                Severity.CRITICAL: int(tr["critical"]),
                Severity.MEDIUM: int(tr["medium"]),
                Severity.LOW: int(tr["low"]),
            }

        rest_time = int(section["rest_time"]) if need_rest else None
        if need_rest and "rest_time" not in section:
            raise RulesConfigError("Sekce pravidla vyžaduje položku 'rest_time'")

        if need_disciplines:
            vals = section.get("disciplines")
            if not isinstance(vals, list) or not vals:
                raise RulesConfigError(
                    "Sekce pravidla vyžaduje neprázdný seznam 'disciplines'"
                )
            disciplines = tuple(str(v) for v in vals)
        else:
            disciplines = None

        min_gap_minutes = int(section["min_gap_minutes"]) if need_min_gap else None
        if need_min_gap and "min_gap_minutes" not in section:
            raise RulesConfigError("Sekce pravidla vyžaduje položku 'min_gap_minutes'")

        return RuleConfig(
            enabled=enabled,
            thresholds=thresholds,
            rest_time=rest_time,
            disciplines=disciplines,
            min_gap_minutes=min_gap_minutes,
        )
