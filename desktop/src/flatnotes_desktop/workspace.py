import shutil
from dataclasses import dataclass
from pathlib import Path

from whoosh.fields import ID, KEYWORD, TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser

from .paths import workspace_note_path


@dataclass(frozen=True)
class SearchResult:
    title: str
    path: Path


class WorkspaceService:
    """Recursive Markdown workspace backed by portable Whoosh index."""

    _serializable = False

    def __init__(self, root: Path, index_directory: Path):
        self.root = root.resolve()
        self.index_directory = index_directory
        self.schema = Schema(
            title=TEXT(stored=True),
            path=ID(stored=True, unique=True),
            content=TEXT,
            tags=KEYWORD(lowercase=True),
        )

    def rebuild(self) -> None:
        self.index_directory.mkdir(parents=True, exist_ok=True)
        index = create_in(self.index_directory, self.schema)
        writer = index.writer()
        for path in self.list_files():
            content = path.read_text(encoding="utf-8")
            writer.add_document(
                title=self.title_for(path),
                path=str(path),
                content=content,
                tags=" ".join(self._tags(content)),
            )
        writer.commit()

    def rebuild_index(self) -> None:
        """Delete the current Whoosh index and rebuild it from workspace files."""
        if self.index_directory.is_dir():
            shutil.rmtree(self.index_directory)
        elif self.index_directory.exists():
            self.index_directory.unlink()
        self.rebuild()

    def search(self, term: str) -> list[SearchResult]:
        index = open_dir(self.index_directory)
        parser = MultifieldParser(["title", "content", "tags"], index.schema)
        with index.searcher() as searcher:
            hits = searcher.search(parser.parse(term))
            return [SearchResult(hit["title"], Path(hit["path"])) for hit in hits]

    def create(self, title: str, content: str) -> Path:
        path = workspace_note_path(self.root, title)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(path)
        path.write_text(content, encoding="utf-8", newline="")
        self.rebuild()
        return path

    def rename(self, title: str, new_title: str) -> Path:
        path = workspace_note_path(self.root, title)
        destination = workspace_note_path(self.root, new_title)
        if destination.exists() and destination != path:
            raise FileExistsError(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        path.rename(destination)
        self.rebuild()
        return destination

    def delete(self, title: str) -> None:
        path = workspace_note_path(self.root, title)
        path.unlink()
        self.rebuild()

    def list_files(self) -> list[Path]:
        return sorted(
            path for path in self.root.rglob("*.md") if ".flatnotes" not in path.parts
        )

    def title_for(self, path: Path) -> str:
        return path.relative_to(self.root).with_suffix("").as_posix()

    @staticmethod
    def _tags(content: str) -> list[str]:
        return [word[1:].lower() for word in content.split() if word.startswith("#")]
