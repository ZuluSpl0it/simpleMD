from pathlib import Path

from .files import FileService
from .settings import SettingsStore
from .workspace import WorkspaceService
from .watcher import Fingerprint, changed_since


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
        self._refresh_workspace_for(document.path)
        return self._document_payload(document)

    def save_tab(self, tab: dict) -> dict:
        document = self.file_service.save_external(tab["path"], tab.get("content", ""))
        self._refresh_workspace_for(document.path)
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
        return self._set_workspace(root, index_dir)

    def load_workspace(self) -> dict | None:
        if self.settings is None:
            return None
        saved = self.settings.load().workspace
        if not saved:
            return None
        root = Path(saved).resolve()
        if not root.is_dir():
            return {"workspace": None, "error": "Saved workspace folder is unavailable."}
        return self._set_workspace(root, self.settings.data_directory / "index")

    def _set_workspace(self, root: Path, index_dir: Path) -> dict:
        self.workspace = WorkspaceService(root, index_dir)
        self.workspace.rebuild()
        return {"workspace": str(root)}

    def _refresh_workspace_for(self, path: Path) -> None:
        if self.workspace and self.workspace.root in path.resolve().parents:
            self.workspace.rebuild()

    def search_workspace(self, term: str) -> list[dict]:
        if self.workspace is None:
            return []
        return [{"title": result.title, "path": str(result.path)} for result in self.workspace.search(term)]

    def get_workspace(self) -> str | None:
        return str(self.workspace.root) if self.workspace else None

    def create_workspace_note(self, title: str, content: str) -> dict:
        if self.workspace is None:
            raise ValueError("Select a workspace first.")
        path = self.workspace.create(title, content)
        document = self.file_service.open_external(path)
        payload = self._document_payload(document)
        payload["kind"] = "workspace"
        payload["title"] = self.workspace.title_for(path)
        return payload

    def rename_workspace_note(self, title: str, new_title: str) -> dict:
        if self.workspace is None:
            raise ValueError("Select a workspace first.")
        path = self.workspace.rename(title, new_title)
        document = self.file_service.open_external(path)
        payload = self._document_payload(document)
        payload["kind"] = "workspace"
        payload["title"] = self.workspace.title_for(path)
        return payload

    def delete_workspace_note(self, title: str) -> None:
        if self.workspace is None:
            raise ValueError("Select a workspace first.")
        self.workspace.delete(title)

    def check_file(self, tab: dict) -> dict:
        path = Path(tab["path"])
        if not path.exists():
            return {"state": "missing", "path": str(path)}
        baseline = Fingerprint(int(tab["modified_ns"]), tab["content_hash"])
        return {"state": "changed" if changed_since(path, baseline) else "clean", "path": str(path)}

    @staticmethod
    def _document_payload(document) -> dict:
        return {
            "kind": "external",
            "path": str(document.path),
            "content": document.content,
            # JavaScript Numbers cannot exactly represent nanosecond timestamps.
            # Keep this as a decimal string across the webview boundary.
            "modified_ns": str(document.modified_ns),
            "content_hash": document.content_hash,
        }
