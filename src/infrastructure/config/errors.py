from __future__ import annotations


class ConfigError(ValueError):
    """Base config error."""


class RulesConfigError(ConfigError):
    """Raised when rules config is invalid."""