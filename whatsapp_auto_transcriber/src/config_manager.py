"""Load configuration from YAML files."""

import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = {}

    def load(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f) or {}
        return self.config
