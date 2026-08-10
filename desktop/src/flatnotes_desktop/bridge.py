from pathlib import Path

from .files import FileService
from .settings import SettingsStore
from .workspace import WorkspaceService


class DesktopBridge:
    def __init__(self, window, file_service: FileService, settings=None, workspace=None):
        self.window = window
        self.file_service = file_service
        self.settings = settings
        self.workspace = workspace

    def open_markdown(self) -> dict | None:
        import webview

        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Markdown (*.md)",),
        )
        if not result:
            return None
        return self._document_payload(self.file_service.open_external(result[0]))

    def open_dropped_path(self, path: str) -> dict:
        target = Path(path)
        if target.suffix.lower() != ".md" or not target.is_file():
            return {"error": "Drop a Markdown file (.md)."}
        return self._document_payload(self.file_service.open_external(target))

    def save_as(self, tab: dict) -> dict | None:
        import webview

        result = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=Path(tab.get("path") or "Untitled.md").name,
            file_types=("Markdown (*.md)",),
        )
        if not result:
            return None
        document = self.file_service.save_external(result[0], tab.get("content", ""))
        return self._document_payload(document)

    def save_tab(self, tab: dict) -> dict:
        document = self.file_service.save_external(tab["path"], tab.get("content", ""))
        return self._document_payload(document)

    def select_workspace(self) -> dict | None:
        import webview

        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        if not result:
            return None
        root = Path(result[0]).resolve()
        if not root.is_dir():
            raise ValueError("Select a workspace folder.")
        if self.settings is not None:
            self.settings.save_workspace(str(root))
            index_dir = self.settings.data_directory / "index"
        else:
            index_dir = root / ".flatnotes"
        self.workspace = WorkspaceService(root, index_dir)
        self.workspace.rebuild()
        return {"workspace": str(root)}

    def search_workspace(self, term: str) -> list[dict]:
        if self.workspace is None:
            return []
        return [{"title": result.title, "path": str(result.path)} for result in self.workspace.search(term)]

    @staticmethod
    def _document_payload(document) -> dict:
        return {
            "kind": "external",
            "path": str(document.path),
            "content": document.content,
            "modified_ns": document.modified_ns,
            "content_hash": document.content_hash,
        }
