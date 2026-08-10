import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Fingerprint:
    modified_ns: int
    content_hash: str


def fingerprint(path: Path) -> Fingerprint:
    content = path.read_bytes()
    return Fingerprint(
        modified_ns=path.stat().st_mtime_ns,
        content_hash=hashlib.sha256(content).hexdigest(),
    )


def changed_since(path: Path, baseline: Fingerprint) -> bool:
    return not path.exists() or fingerprint(path) != baseline
