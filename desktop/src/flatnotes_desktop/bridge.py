from pathlib import Path

from .files import FileService


class DesktopBridge:
    def __init__(self, window, file_service: FileService):
        self.window = window
        self.file_service = file_service

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

    @staticmethod
    def _document_payload(document) -> dict:
        return {
            "kind": "external",
            "path": str(document.path),
            "content": document.content,
            "modified_ns": document.modified_ns,
            "content_hash": document.content_hash,
        }
