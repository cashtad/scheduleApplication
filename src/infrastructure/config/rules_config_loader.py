from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from src.domain import Severity, RuleConfig, RulesConfig
from .errors import RulesConfigError


class YamlRulesConfigLoader:
    @staticmethod
    def load_from_file(path: str | Path) -> RulesConfig:
        file_path = Path(path)
        if not file_path.exists():
            raise RulesConfigError(f"Rules config file not found: {file_path}")

        try:
            with file_path.open("r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except Exception as exc:
            raise RulesConfigError(f"Failed to read rules config: {exc}") from exc

        if not isinstance(raw, Mapping):
            raise RulesConfigError("Top-level YAML must be a mapping")

        return RulesConfig(
            max_continuous_dancing=YamlRulesConfigLoader._parse_rule_config(
                raw, "max_continuous_dancing"
            ),
            costume_change_time=YamlRulesConfigLoader._parse_rule_config(
                raw, "costume_change_time"
            ),
            max_continuous_judging=YamlRulesConfigLoader._parse_rule_config(
                raw, "max_continuous_judging"
            ),
            max_gap_between_performances=YamlRulesConfigLoader._parse_rule_config(
                raw, "max_gap_between_performances"
            ),
            simultaneous_dancing=YamlRulesConfigLoader._parse_rule_config(
                raw, "simultaneous_dancing"
            ),
            simultaneous_judging=YamlRulesConfigLoader._parse_rule_config(
                raw, "simultaneous_judging"
            ),
        )

    @staticmethod
    def _parse_rule_config(config: Mapping[str, Any], key: str) -> RuleConfig:
        raw_cfg = config.get(key)
        if raw_cfg is None:
            raise RulesConfigError(f"Missing required rule config section '{key}'")
        if not isinstance(raw_cfg, Mapping):
            raise RulesConfigError(f"Rule section '{key}' must be a mapping")

        enabled = bool(raw_cfg.get("enabled", True))
        thresholds = YamlRulesConfigLoader._parse_thresholds(
            raw_cfg.get("thresholds"), key
        )

        rest_time = raw_cfg.get("rest_time")
        if rest_time is not None:
            rest_time = int(rest_time)

        min_gap_minutes = raw_cfg.get("min_gap_minutes")
        if min_gap_minutes is not None:
            min_gap_minutes = int(min_gap_minutes)

        disciplines_raw = raw_cfg.get("disciplines")
        disciplines: tuple[str, ...] | None = None
        if disciplines_raw is not None:
            if not isinstance(disciplines_raw, list):
                raise RulesConfigError(f"'{key}.disciplines' must be a list")
            disciplines = tuple(str(item) for item in disciplines_raw)

        return RuleConfig(
            enabled=enabled,
            thresholds=thresholds,
            rest_time=rest_time,
            disciplines=disciplines,
            min_gap_minutes=min_gap_minutes,
        )

    @staticmethod
    def _parse_thresholds(value: Any, key: str) -> dict[Severity, int] | None:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise RulesConfigError(f"'{key}.thresholds' must be a mapping")

        parsed: dict[Severity, int] = {}
        for raw_severity, raw_limit in value.items():
            severity = YamlRulesConfigLoader._parse_severity(raw_severity)
            parsed[severity] = int(raw_limit)
        return parsed

    @staticmethod
    def _parse_severity(value: Any) -> Severity:
        if isinstance(value, Severity):
            return value
        if not isinstance(value, str):
            raise RulesConfigError(
                f"Severity must be string, got: {type(value).__name__}"
            )

        normalized = value.strip().lower()
        mapping = {
            "critical": Severity.CRITICAL,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
        }
        if normalized not in mapping:
            raise RulesConfigError(
                f"Unknown severity '{value}'. Expected one of: {', '.join(mapping.keys())}"
            )
        return mapping[normalized]
