import json
import os
from pathlib import Path

from .models import Settings


class SettingsStore:
    _serializable = False
    DEFAULT_FONT_SIZE = 17
    DEFAULT_CODE_FONT_SIZE = 13
    FONT_SIZE_RANGE = range(12, 33)
    CODE_FONT_SIZE_RANGE = range(10, 25)

    def __init__(self, data_directory: Path):
        self.data_directory = data_directory
        self.path = data_directory / "settings.json"

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        theme = payload.get("theme")
        return Settings(
            workspace=payload.get("workspace"),
            theme=theme if theme in {"dark", "light"} else "dark",
            font_size=self._font_size(
                payload.get("font_size"), self.DEFAULT_FONT_SIZE, self.FONT_SIZE_RANGE
            ),
            code_font_size=self._font_size(
                payload.get("code_font_size"),
                self.DEFAULT_CODE_FONT_SIZE,
                self.CODE_FONT_SIZE_RANGE,
            ),
        )

    def save_workspace(self, workspace: str | None) -> Settings:
        current = self.load()
        return self._save(
            workspace=workspace,
            theme=current.theme,
            font_size=current.font_size,
            code_font_size=current.code_font_size,
        )

    def save_theme(self, theme: str) -> Settings:
        if theme not in {"dark", "light"}:
            raise ValueError("Theme must be 'dark' or 'light'.")
        current = self.load()
        return self._save(
            workspace=current.workspace,
            theme=theme,
            font_size=current.font_size,
            code_font_size=current.code_font_size,
        )

    @staticmethod
    def _font_size(value, default: int, allowed: range) -> int:
        if isinstance(value, int) and not isinstance(value, bool) and value in allowed:
            return value
        return default

    def _save(
        self,
        *,
        workspace: str | None,
        theme: str,
        font_size: int,
        code_font_size: int,
    ) -> Settings:
        self.data_directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "workspace": workspace,
                    "theme": theme,
                    "font_size": font_size,
                    "code_font_size": code_font_size,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
        return Settings(
            workspace=workspace,
            theme=theme,
            font_size=font_size,
            code_font_size=code_font_size,
        )
