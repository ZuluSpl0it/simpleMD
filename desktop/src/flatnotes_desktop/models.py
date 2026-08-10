from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    workspace: str | None = None


@dataclass(frozen=True)
class Document:
    path: Path
    content: str
    modified_ns: int
    content_hash: str
