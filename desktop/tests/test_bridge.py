from pathlib import Path


class FakeWindow:
    def __init__(self, result):
        self.result = result
        self.dialog_calls = []

    def create_file_dialog(self, *_args, **_kwargs):
        self.dialog_calls.append((_args, _kwargs))
        return self.result


class FakeThread:
    created = []

    def __init__(self, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.started = False
        type(self).created.append(self)

    def start(self):
        self.started = True


def test_frontend_can_record_a_startup_event():
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    events = []
    bridge = DesktopBridge(FakeWindow(None), FileService(), trace=events.append)

    bridge.startup_event("frontend-mounted")

    assert events == ["frontend-mounted"]


def test_launch_paths_are_returned_once():
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    bridge = DesktopBridge(None, FileService(), launch_paths=["one.md", "two.md"])

    assert bridge.get_launch_paths() == ["one.md", "two.md"]
    assert bridge.get_launch_paths() == []


def test_bridge_reads_and_changes_theme(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    bridge = DesktopBridge(None, FileService(), settings=SettingsStore(tmp_path / "data"))

    assert bridge.get_theme() == "dark"
    assert bridge.set_theme("light") == "light"
    assert bridge.get_theme() == "light"


def test_bridge_reads_font_settings(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"font_size":{"text":16,"code":11,'
        '"heading_multiplier":{"h1":2.5}}}',
        encoding="utf-8",
    )

    settings = DesktopBridge(None, FileService(), settings=store).get_font_settings()

    assert settings["text"] == 16
    assert settings["code"] == 11
    assert settings["heading_multiplier"]["h1"] == 2.5
    assert set(settings["heading_multiplier"]) == {
        f"h{level}" for level in range(1, 7)
    }


def test_bridge_state_objects_are_not_recursively_exposed(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    bridge = DesktopBridge(
        None,
        FileService(),
        settings=SettingsStore(tmp_path / "data"),
    )

    assert bridge.file_service._serializable is False
    assert bridge.settings._serializable is False


def test_restored_workspace_is_not_recursively_exposed(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    bridge = DesktopBridge(
        None,
        FileService(),
        settings=SettingsStore(tmp_path / "data"),
    )
    bridge.restore_workspace()

    assert bridge.workspace._serializable is False


def test_open_dialog_returns_external_document(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    path = tmp_path / "outside.md"
    path.write_text("body", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow((str(path),)), FileService())

    assert bridge.open_markdown()["kind"] == "external"


def test_open_markdown_dialog_starts_in_workspace(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "outside.md"
    path.write_text("body", encoding="utf-8")
    window = FakeWindow((str(path),))
    bridge = DesktopBridge(window, FileService(), workspace=WorkspaceService(root, tmp_path / "index"))

    bridge.open_markdown()

    assert window.dialog_calls[0][1]["directory"] == str(root.resolve())


def test_open_external_link_uses_browser_adapter(monkeypatch):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    import webbrowser

    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    bridge = DesktopBridge(FakeWindow(None), FileService())

    assert bridge.open_external_link("https://example.com/docs") is True
    assert opened == ["https://example.com/docs"]


def test_open_markdown_link_resolves_relative_to_current_file(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    source = tmp_path / "guide.md"
    target = tmp_path / "parts" / "setup.md"
    target.parent.mkdir()
    source.write_text("body", encoding="utf-8")
    target.write_text("# Install", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow(None), FileService())

    result = bridge.open_markdown_link(str(source), "parts/setup.md#install")

    assert result["path"] == str(target.resolve())
    assert result["content"] == "# Install"


def test_open_markdown_link_rejects_missing_or_non_markdown_targets(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    source = tmp_path / "guide.md"
    source.write_text("body", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow(None), FileService())

    assert "error" in bridge.open_markdown_link(str(source), "missing.md")
    assert "error" in bridge.open_markdown_link(str(source), "image.png")


def test_windows_drive_links_decode_into_local_paths():
    from flatnotes_desktop.bridge import _is_windows_absolute_path

    assert _is_windows_absolute_path(r"C:\src\dist\Flatnotes\workspace\pokeno_readme.md") is True


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


def test_select_workspace_dialog_starts_in_current_workspace(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore
    from flatnotes_desktop.workspace import WorkspaceService

    current = tmp_path / "current"
    selected = tmp_path / "selected"
    current.mkdir()
    selected.mkdir()
    window = FakeWindow((str(selected),))
    bridge = DesktopBridge(
        window,
        FileService(),
        settings=SettingsStore(tmp_path / "data"),
        workspace=WorkspaceService(current, tmp_path / "index"),
    )

    bridge.select_workspace()

    assert window.dialog_calls[0][1]["directory"] == str(current.resolve())


def test_select_workspace_returns_before_background_index_rebuild(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.settings import SettingsStore
    from flatnotes_desktop.files import FileService

    FakeThread.created = []
    workspace = tmp_path / "notes"
    workspace.mkdir()
    bridge = DesktopBridge(
        FakeWindow((str(workspace),)),
        FileService(),
        settings=SettingsStore(tmp_path / "data"),
        thread_factory=FakeThread,
    )

    result = bridge.select_workspace()

    assert result["workspace"] == str(workspace.resolve())
    assert bridge.get_index_status()["indexing"] is True
    assert FakeThread.created[0].started is True
    assert bridge.search_workspace("anything") == []

    FakeThread.created[0].target(*FakeThread.created[0].args)

    assert bridge.get_index_status() == {
        "workspace": str(workspace.resolve()),
        "indexing": False,
        "error": None,
    }


def test_delayed_rebuild_skips_workspace_that_is_no_longer_current(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore
    from flatnotes_desktop.workspace import WorkspaceService

    FakeThread.created = []
    old_root = tmp_path / "old"
    new_root = tmp_path / "new"
    old_root.mkdir()
    new_root.mkdir()
    settings = SettingsStore(tmp_path / "data")
    settings.save_workspace(str(new_root))
    old_service = WorkspaceService(old_root, tmp_path / "index")
    bridge = DesktopBridge(
        FakeWindow(None),
        FileService(),
        settings=settings,
        workspace=old_service,
        thread_factory=FakeThread,
    )
    bridge.restore_workspace()

    assert bridge.rebuild_workspace_if_current(old_service) is False
    assert FakeThread.created == []


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


def test_rebuild_index_requires_a_selected_workspace(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService

    bridge = DesktopBridge(FakeWindow(None), FileService())

    assert bridge.rebuild_index() == {
        "workspace": None,
        "error": "Select a workspace first.",
    }


def test_rebuild_index_rebuilds_the_selected_workspace(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.workspace import WorkspaceService

    workspace = tmp_path / "notes"
    workspace.mkdir()
    (workspace / "plan.md").write_text("release", encoding="utf-8")
    service = WorkspaceService(workspace, tmp_path / "index")
    service.rebuild()
    (service.index_directory / "stale.marker").write_text("stale", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow(None), FileService(), workspace=service)

    result = bridge.rebuild_index()

    assert result == {"workspace": str(workspace.resolve())}
    assert not (service.index_directory / "stale.marker").exists()
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


def test_restore_workspace_defaults_to_portable_workspace_folder(tmp_path: Path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    settings = SettingsStore(tmp_path / "data")
    bridge = DesktopBridge(FakeWindow(None), FileService(), settings=settings)

    result = bridge.restore_workspace()

    expected = (tmp_path / "workspace").resolve()
    assert result["workspace"] == str(expected)
    assert expected.is_dir()
    assert settings.load().workspace == str(expected)


def test_restore_workspace_does_not_build_index_before_the_window_opens(tmp_path: Path, monkeypatch):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore
    from flatnotes_desktop.workspace import WorkspaceService

    workspace = tmp_path / "notes"
    workspace.mkdir()
    settings = SettingsStore(tmp_path / "data")
    settings.save_workspace(str(workspace))
    bridge = DesktopBridge(FakeWindow(None), FileService(), settings=settings)

    monkeypatch.setattr(WorkspaceService, "rebuild", lambda _self: (_ for _ in ()).throw(AssertionError("should rebuild later")))

    assert bridge.restore_workspace()["workspace"] == str(workspace.resolve())


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


def test_bridge_reads_heading_colors(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"heading_colors":{"dark":{"h1":"#010203"},'
        '"light":{"h6":"#A0B0C0"}}}',
        encoding="utf-8",
    )
    bridge = DesktopBridge(None, FileService(), settings=store)

    colors = bridge.get_heading_colors()

    assert colors["dark"]["h1"] == "#010203"
    assert colors["light"]["h6"] == "#A0B0C0"
    assert set(colors["dark"]) == {f"h{level}" for level in range(1, 7)}


def test_bridge_heading_colors_fall_back_without_settings():
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.models import default_heading_colors

    bridge = DesktopBridge(None, FileService())

    assert bridge.get_heading_colors() == default_heading_colors()
