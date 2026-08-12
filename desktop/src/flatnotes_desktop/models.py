from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    workspace: str | None = None
    theme: str = "dark"


@dataclass(frozen=True)
class Document:
    path: Path
    content: str
    modified_ns: int
    content_hash: str
