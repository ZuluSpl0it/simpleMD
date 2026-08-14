from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    workspace: str | None = None
    theme: str = "dark"
    font_size: int = 17
    code_font_size: int = 13


@dataclass(frozen=True)
class Document:
    path: Path
    content: str
    modified_ns: int
    content_hash: str
