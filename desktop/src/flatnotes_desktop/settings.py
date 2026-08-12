import json
import os
from pathlib import Path

from .models import Settings


class SettingsStore:
    _serializable = False

    def __init__(self, data_directory: Path):
        self.data_directory = data_directory
        self.path = data_directory / "settings.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        theme = payload.get("theme")
        return Settings(workspace=payload.get("workspace"), theme=theme if theme in {"dark", "light"} else "dark")

    def save_workspace(self, workspace: str | None) -> Settings:
        current = self.load()
        return self._save(workspace=workspace, theme=current.theme)

    def save_theme(self, theme: str) -> Settings:
        if theme not in {"dark", "light"}:
            raise ValueError("Theme must be 'dark' or 'light'.")
        current = self.load()
        return self._save(workspace=current.workspace, theme=theme)

    def _save(self, *, workspace: str | None, theme: str) -> Settings:
        self.data_directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"workspace": workspace, "theme": theme}, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
        return Settings(workspace=workspace, theme=theme)
