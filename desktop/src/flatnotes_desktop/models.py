from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_HEADING_COLORS = {
    "dark": {
        "h1": "#FCA5A5",
        "h2": "#FDBA74",
        "h3": "#FDE68A",
        "h4": "#86EFAC",
        "h5": "#93C5FD",
        "h6": "#C4B5FD",
    },
    "light": {
        "h1": "#B91C1C",
        "h2": "#C2410C",
        "h3": "#A16207",
        "h4": "#15803D",
        "h5": "#1D4ED8",
        "h6": "#6D28D9",
    },
}


def default_heading_colors() -> dict[str, dict[str, str]]:
    return {theme: dict(palette) for theme, palette in DEFAULT_HEADING_COLORS.items()}


DEFAULT_FONT_SIZES = {
    "text": 14,
    "code": 12,
    "heading_multiplier": {
        "h1": 2.4,
        "h2": 2.08,
        "h3": 1.78,
        "h4": 1.5,
        "h5": 1.29,
        "h6": 1.15,
    },
}


def default_font_sizes() -> dict[str, int | dict[str, float]]:
    return {
        "text": DEFAULT_FONT_SIZES["text"],
        "code": DEFAULT_FONT_SIZES["code"],
        "heading_multiplier": dict(DEFAULT_FONT_SIZES["heading_multiplier"]),
    }


@dataclass(frozen=True)
class Settings:
    workspace: str | None = None
    theme: str = "dark"
    font_size: dict[str, int | dict[str, float]] = field(
        default_factory=default_font_sizes
    )
    heading_colors: dict[str, dict[str, str]] = field(
        default_factory=default_heading_colors
    )


@dataclass(frozen=True)
class Document:
    path: Path
    content: str
    modified_ns: int
    content_hash: str
