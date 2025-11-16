import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

@dataclass
class AppConfig:
    files: Dict[str, Dict[str, Any]]
    columns: Dict[str, Dict[str, str]]

class ConfigLoader:
    def __init__(self, config_path: str):
        self._path = Path(config_path)

    def load(self) -> AppConfig:
        with self._path.open(encoding="utf-8") as fh:
            payload = yaml.safe_load(fh)
        return AppConfig(**payload)