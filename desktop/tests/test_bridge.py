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


def test_select_workspace_persists_folder(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.settings import SettingsStore
    from flatnotes_desktop.files import FileService

    workspace = tmp_path / "notes"
    workspace.mkdir()
    bridge = DesktopBridge(
        FakeWindow((str(workspace),)),
        FileService(),
        settings=SettingsStore(tmp_path / "data"),
    )

    result = bridge.select_workspace()

    assert result["workspace"] == str(workspace.resolve())


def test_search_workspace_returns_relative_result(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.workspace import WorkspaceService

    workspace = tmp_path / "notes"
    workspace.mkdir()
    (workspace / "plan.md").write_text("release", encoding="utf-8")
    service = WorkspaceService(workspace, tmp_path / "index")
    service.rebuild()
    bridge = DesktopBridge(FakeWindow(None), FileService(), workspace=service)

    assert bridge.search_workspace("release")[0]["title"] == "plan"


def test_check_file_reports_external_change(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    path = tmp_path / "note.md"
    path.write_text("one", encoding="utf-8")
    document = FileService().open_external(path)
    path.write_text("two", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow(None), FileService())

    assert bridge.check_file({"path": str(path), "modified_ns": document.modified_ns, "content_hash": document.content_hash})["state"] == "changed"


def test_check_file_accepts_an_unchanged_crlf_file(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    path = tmp_path / "windows-note.md"
    path.write_bytes(b"first line\r\nsecond line\r\n")
    document = FileService().open_external(path)
    bridge = DesktopBridge(FakeWindow(None), FileService())

    assert bridge.check_file({"path": str(path), "modified_ns": document.modified_ns, "content_hash": document.content_hash})["state"] == "clean"


def test_document_payload_preserves_nanosecond_timestamp_as_string(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    path = tmp_path / "precise-timestamp.md"
    path.write_text("body", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow((str(path),)), FileService())

    document = bridge.open_markdown()

    assert document["modified_ns"] == str(path.stat().st_mtime_ns)
    assert bridge.check_file(document)["state"] == "clean"


def test_load_workspace_uses_saved_folder(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    workspace = tmp_path / "notes"
    workspace.mkdir()
    settings = SettingsStore(tmp_path / "data")
    settings.save_workspace(str(workspace))
    bridge = DesktopBridge(FakeWindow(None), FileService(), settings=settings)

    result = bridge.load_workspace()

    assert result["workspace"] == str(workspace.resolve())


def test_create_workspace_note_returns_saved_document(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    service = WorkspaceService(root, tmp_path / "index")
    bridge = DesktopBridge(FakeWindow(None), FileService(), workspace=service)

    result = bridge.create_workspace_note("Projects/plan", "body")

    assert result["kind"] == "workspace"
    assert (root / "Projects" / "plan.md").read_text() == "body"
