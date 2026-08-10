from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    workspace: str | None = None
