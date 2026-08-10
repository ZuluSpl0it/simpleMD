from pathlib import Path


def test_recursive_search_keeps_relative_title(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    note = root / "Projects" / "alpha" / "plan.md"
    note.parent.mkdir(parents=True)
    note.write_text("release roadmap #release", encoding="utf-8")

    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    assert [item.title for item in service.search("release")] == [
        "Projects/alpha/plan"
    ]


def test_rename_preserves_nested_workspace_containment(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    service = WorkspaceService(root, tmp_path / "index")
    service.create("A/old", "body")

    service.rename("A/old", "B/new")

    assert (root / "B" / "new.md").exists()
    assert not (root / "A" / "old.md").exists()


def test_delete_removes_note_from_search(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    service = WorkspaceService(root, tmp_path / "index")
    service.create("plan", "release roadmap")
    service.delete("plan")

    assert service.search("release") == []
