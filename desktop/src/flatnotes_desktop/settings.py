import json
import math
import os
import re
from pathlib import Path

from .models import Settings, default_font_sizes, default_heading_colors


class SettingsStore:
    _serializable = False
    PIXEL_SIZE_RANGE = range(8, 73)
    HEADING_MULTIPLIER_RANGE = (0.5, 4.0)
    HEADING_LEVELS = tuple(f"h{level}" for level in range(1, 7))
    LEGACY_HEADING_MULTIPLIERS = {
        "h1": 2.0,
        "h2": 1.7059,
        "h3": 1.4706,
        "h4": 1.2353,
        "h5": 1.0588,
        "h6": 0.9412,
    }

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
            font_size=self._font_sizes(
                payload.get("font_size"), payload.get("code_font_size")
            ),
            heading_colors=self._heading_colors(payload.get("heading_colors")),
        )

    def save_workspace(self, workspace: str | None) -> Settings:
        current = self.load()
        return self._save(
            workspace=workspace,
            theme=current.theme,
            font_size=current.font_size,
            heading_colors=current.heading_colors,
        )

    def save_theme(self, theme: str) -> Settings:
        if theme not in {"dark", "light"}:
            raise ValueError("Theme must be 'dark' or 'light'.")
        current = self.load()
        return self._save(
            workspace=current.workspace,
            theme=theme,
            font_size=current.font_size,
            heading_colors=current.heading_colors,
        )

    @classmethod
    def _pixel_size(cls, value, default: int) -> int:
        if (
            isinstance(value, int)
            and not isinstance(value, bool)
            and value in cls.PIXEL_SIZE_RANGE
        ):
            return value
        return default

    @classmethod
    def _multiplier(cls, value, default: float) -> float:
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and cls.HEADING_MULTIPLIER_RANGE[0]
            <= value
            <= cls.HEADING_MULTIPLIER_RANGE[1]
        ):
            return float(value)
        return default

    @classmethod
    def _font_sizes(cls, value, legacy_code_size) -> dict[str, int | dict[str, float]]:
        defaults = default_font_sizes()
        if isinstance(value, int) and not isinstance(value, bool):
            if value not in cls.PIXEL_SIZE_RANGE:
                return defaults
            return {
                "text": value,
                "code": cls._pixel_size(legacy_code_size, 13),
                "heading_multiplier": dict(cls.LEGACY_HEADING_MULTIPLIERS),
            }
        if not isinstance(value, dict):
            return defaults
        multipliers = value.get("heading_multiplier")
        return {
            "text": cls._pixel_size(value.get("text"), defaults["text"]),
            "code": cls._pixel_size(value.get("code"), defaults["code"]),
            "heading_multiplier": {
                heading: cls._multiplier(
                    multipliers.get(heading) if isinstance(multipliers, dict) else None,
                    defaults["heading_multiplier"][heading],
                )
                for heading in cls.HEADING_LEVELS
            },
        }

    @classmethod
    def _heading_colors(cls, value) -> dict[str, dict[str, str]]:
        colors = default_heading_colors()
        if not isinstance(value, dict):
            return colors
        for theme in ("dark", "light"):
            palette = value.get(theme)
            if not isinstance(palette, dict):
                continue
            for heading in cls.HEADING_LEVELS:
                color = palette.get(heading)
                if isinstance(color, str) and re.fullmatch(
                    r"#[0-9A-Fa-f]{6}", color
                ):
                    colors[theme][heading] = color
        return colors

    def _save(
        self,
        *,
        workspace: str | None,
        theme: str,
        font_size: dict[str, int | dict[str, float]],
        heading_colors: dict[str, dict[str, str]],
    ) -> Settings:
        self.data_directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "workspace": workspace,
                    "theme": theme,
                    "font_size": font_size,
                    "heading_colors": heading_colors,
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
            font_size={
                "text": font_size["text"],
                "code": font_size["code"],
                "heading_multiplier": dict(font_size["heading_multiplier"]),
            },
            heading_colors={
                theme: dict(palette) for theme, palette in heading_colors.items()
            },
        )
