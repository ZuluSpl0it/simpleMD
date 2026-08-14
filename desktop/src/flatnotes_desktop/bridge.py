import os
from pathlib import Path
from threading import Lock, RLock, Thread
import sys
import webbrowser
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from .files import FileService
from .models import default_font_sizes, default_heading_colors
from .settings import SettingsStore
from .workspace import WorkspaceService
from .watcher import Fingerprint, changed_since


def _is_windows_absolute_path(value: str) -> bool:
    return (len(value) >= 3 and value[1] == ":" and value[2] in "\\/") or value.startswith("\\\\")


class DesktopBridge:
    def __init__(self, window, file_service: FileService, settings=None, workspace=None, trace=None, thread_factory=None):
        self.window = window
        self.file_service = file_service
        self.settings = settings
        self.workspace = workspace
        self.trace = trace or (lambda _event: None)
        self._thread_factory = thread_factory or Thread
        self._index_state_lock = RLock()
        self._index_operation_lock = Lock()
        self._index_generation = 0
        self._indexing = False
        self._index_error = None

    def startup_event(self, event: str) -> None:
        self.trace(event)

    def get_theme(self) -> str:
        return self.settings.load().theme if self.settings is not None else "dark"

    def get_font_settings(self) -> dict[str, int | dict[str, float]]:
        if self.settings is None:
            return default_font_sizes()
        font_size = self.settings.load().font_size
        return {
            "text": font_size["text"],
            "code": font_size["code"],
            "heading_multiplier": dict(font_size["heading_multiplier"]),
        }

    def get_heading_colors(self) -> dict[str, dict[str, str]]:
        if self.settings is None:
            return default_heading_colors()
        colors = self.settings.load().heading_colors
        return {theme: dict(palette) for theme, palette in colors.items()}

    def set_theme(self, theme: str) -> str:
        if self.settings is None:
            return "dark"
        return self.settings.save_theme(theme).theme

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

    @staticmethod
    def open_external_link(url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Only web links can open in the browser.")
        return bool(webbrowser.open(url))

    def open_markdown_link(self, current_path: str, href: str) -> dict:
        decoded_href = unquote(href)
        if _is_windows_absolute_path(decoded_href):
            target = Path(decoded_href.split("#", 1)[0]).resolve()
            parsed = None
        else:
            parsed = urlparse(href)
            target = None
        if parsed is not None and parsed.scheme in {"http", "https"}:
            self.open_external_link(href)
            return {"opened": True}
        if parsed is not None and parsed.scheme and parsed.scheme != "file":
            return {"error": "Unsupported link type."}
        if target is None and parsed.scheme == "file":
            target = Path(url2pathname(unquote(parsed.path)))
        elif target is None:
            target = Path(current_path).resolve().parent / unquote(parsed.path)
        target = target.resolve()
        if not target.exists():
            return {"error": f"Link target does not exist: {target}"}
        if target.suffix.lower() == ".md":
            try:
                return self._document_payload(self.file_service.open_external(target))
            except (OSError, ValueError) as error:
                return {"error": str(error)}
        try:
            if sys.platform == "win32":
                os.startfile(str(target))
            else:
                webbrowser.open(target.as_uri())
            return {"opened": True}
        except (OSError, ValueError) as error:
            return {"error": str(error)}

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
        result = self.restore_workspace()
        if result and self.workspace:
            self._queue_workspace_rebuild(self.workspace)
        return result

    def restore_workspace(self) -> dict | None:
        """Restore the selected folder without blocking startup on indexing."""
        if self.settings is None:
            return None
        saved = self.settings.load().workspace
        if not saved:
            root = (self.settings.data_directory.parent / "workspace").resolve()
            root.mkdir(parents=True, exist_ok=True)
            self.settings.save_workspace(str(root))
        else:
            root = Path(saved).resolve()
        if not root.is_dir():
            return {"workspace": None, "error": "Saved workspace folder is unavailable."}
        with self._index_state_lock:
            self.workspace = WorkspaceService(root, self.settings.data_directory / "index")
            self._index_generation += 1
            self._indexing = True
            self._index_error = None
        return {"workspace": str(root)}

    def _set_workspace(self, root: Path, index_dir: Path) -> dict:
        workspace = WorkspaceService(root, index_dir)
        with self._index_state_lock:
            self.workspace = workspace
            self._queue_workspace_rebuild_locked(workspace)
        return {"workspace": str(root)}

    def _refresh_workspace_for(self, path: Path) -> None:
        with self._index_state_lock:
            workspace = self.workspace
            if workspace and workspace.root in path.resolve().parents:
                self._queue_workspace_rebuild_locked(workspace)

    def search_workspace(self, term: str) -> list[dict]:
        with self._index_operation_lock:
            with self._index_state_lock:
                if self.workspace is None or self._indexing:
                    return []
                workspace = self.workspace
                generation = self._index_generation
            results = [{"title": result.title, "path": str(result.path)} for result in workspace.search(term)]
            with self._index_state_lock:
                if generation != self._index_generation or workspace is not self.workspace:
                    return []
            return results

    def rebuild_index(self) -> dict:
        with self._index_operation_lock:
            with self._index_state_lock:
                if self.workspace is None:
                    return {"workspace": None, "error": "Select a workspace first."}
                workspace = self.workspace
                self._index_generation += 1
                generation = self._index_generation
                self._indexing = True
                self._index_error = None
            try:
                workspace.rebuild_index()
            except Exception as error:
                with self._index_state_lock:
                    if generation == self._index_generation:
                        self._indexing = False
                        self._index_error = str(error)
                raise
            with self._index_state_lock:
                if generation == self._index_generation:
                    self._indexing = False
            return {"workspace": str(workspace.root)}

    def get_index_status(self) -> dict:
        with self._index_state_lock:
            return {
                "workspace": str(self.workspace.root) if self.workspace else None,
                "indexing": self._indexing,
                "error": self._index_error,
            }

    def rebuild_workspace_if_current(self, workspace) -> bool:
        """Run the delayed startup rebuild only if its workspace is still active."""
        with self._index_state_lock:
            if workspace is not self.workspace:
                return False
            self._index_generation += 1
            generation = self._index_generation
            self._indexing = True
            self._index_error = None
        self._run_index_rebuild(workspace, generation)
        return True

    def _queue_workspace_rebuild(self, workspace) -> bool:
        with self._index_state_lock:
            if workspace is not self.workspace:
                return False
            self._queue_workspace_rebuild_locked(workspace)
            return True

    def _queue_workspace_rebuild_locked(self, workspace) -> None:
        self._index_generation += 1
        generation = self._index_generation
        self._indexing = True
        self._index_error = None
        thread = self._thread_factory(
            target=self._run_index_rebuild,
            args=(workspace, generation),
            daemon=True,
        )
        thread.start()

    def _run_index_rebuild(self, workspace, generation: int) -> None:
        with self._index_operation_lock:
            with self._index_state_lock:
                if generation != self._index_generation:
                    return
            error = None
            try:
                workspace.rebuild()
            except Exception as caught:
                error = caught
            with self._index_state_lock:
                if generation != self._index_generation:
                    return
                self._indexing = False
                self._index_error = str(error) if error else None

    def get_workspace(self) -> str | None:
        with self._index_state_lock:
            return str(self.workspace.root) if self.workspace else None

    def create_workspace_note(self, title: str, content: str) -> dict:
        with self._index_operation_lock:
            with self._index_state_lock:
                workspace = self.workspace
            if workspace is None:
                raise ValueError("Select a workspace first.")
            path = workspace.create(title, content)
        document = self.file_service.open_external(path)
        payload = self._document_payload(document)
        payload["kind"] = "workspace"
        payload["title"] = workspace.title_for(path)
        return payload

    def rename_workspace_note(self, title: str, new_title: str) -> dict:
        with self._index_operation_lock:
            with self._index_state_lock:
                workspace = self.workspace
            if workspace is None:
                raise ValueError("Select a workspace first.")
            path = workspace.rename(title, new_title)
        document = self.file_service.open_external(path)
        payload = self._document_payload(document)
        payload["kind"] = "workspace"
        payload["title"] = workspace.title_for(path)
        return payload

    def delete_workspace_note(self, title: str) -> None:
        with self._index_operation_lock:
            with self._index_state_lock:
                workspace = self.workspace
            if workspace is None:
                raise ValueError("Select a workspace first.")
            workspace.delete(title)

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
