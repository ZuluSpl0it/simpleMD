import json
import os
from pathlib import Path

from .models import Settings


class SettingsStore:
    def __init__(self, data_directory: Path):
        self.data_directory = data_directory
        self.path = data_directory / "settings.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return Settings(workspace=payload.get("workspace"))

    def save_workspace(self, workspace: str | None) -> Settings:
        self.data_directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"workspace": workspace}, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
        return Settings(workspace=workspace)
