import hashlib
import os
from pathlib import Path

from .models import Document


class FileService:
    """Read and write a user-selected external Markdown file exactly in place."""

    def open_external(self, path: Path | str) -> Document:
        target = self._existing_markdown(path)
        content = target.read_text(encoding="utf-8")
        return self._document(target, content)

    def save_external(self, path: Path | str, content: str) -> Document:
        target = self._markdown_destination(path)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(content, encoding="utf-8", newline="")
        os.replace(temporary, target)
        return self._document(target, content)

    @staticmethod
    def _existing_markdown(path: Path | str) -> Path:
        supplied = Path(path)
        if supplied.suffix.lower() != ".md":
            raise ValueError("Select a Markdown file (.md).")
        target = supplied.resolve(strict=True)
        if not target.is_file():
            raise ValueError("Select a Markdown file (.md).")
        return target

    @staticmethod
    def _markdown_destination(path: Path | str) -> Path:
        target = Path(path).resolve(strict=False)
        if target.suffix.lower() != ".md":
            raise ValueError("Save destination must be a Markdown file (.md).")
        return target

    @staticmethod
    def _document(path: Path, content: str) -> Document:
        return Document(
            path=path,
            content=content,
            modified_ns=path.stat().st_mtime_ns,
            # Fingerprints are compared with watcher.fingerprint(), which hashes
            # on-disk bytes.  Hash bytes here too: read_text() normalizes CRLF
            # to LF, so hashing the decoded text would report unchanged Windows
            # files as externally modified forever.
            content_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
