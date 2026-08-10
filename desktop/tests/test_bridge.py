from pathlib import Path


class FakeWindow:
    def __init__(self, result):
        self.result = result

    def create_file_dialog(self, *_args, **_kwargs):
        return self.result


def test_open_dialog_returns_external_document(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    path = tmp_path / "outside.md"
    path.write_text("body", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow((str(path),)), FileService())

    assert bridge.open_markdown()["kind"] == "external"


def test_drop_rejects_folder_and_non_markdown(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    bridge = DesktopBridge(FakeWindow(None), FileService())

    assert bridge.open_dropped_path(str(tmp_path)) == {
        "error": "Drop a Markdown file (.md)."
    }


def test_save_as_writes_selected_markdown_path(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    destination = tmp_path / "saved.md"
    bridge = DesktopBridge(FakeWindow((str(destination),)), FileService())

    result = bridge.save_as({"content": "body"})

    assert destination.read_text(encoding="utf-8") == "body"
    assert result["path"] == str(destination.resolve())
