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


def test_rebuild_index_removes_stale_index_files(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "plan.md").write_text("release roadmap", encoding="utf-8")
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    stale_file = service.index_directory / "stale.marker"
    stale_file.write_text("stale", encoding="utf-8")
    service.rebuild_index()

    assert not stale_file.exists()
    assert [item.title for item in service.search("release")] == ["plan"]


def test_rebuild_index_refreshes_paths_after_an_external_move(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    original = root / "plan.md"
    original.write_text("release roadmap", encoding="utf-8")
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    moved = root / "archive" / "plan.md"
    moved.parent.mkdir()
    original.rename(moved)
    service.rebuild_index()

    result = service.search("release")
    assert [item.path for item in result] == [moved]


def test_search_matches_technical_identifier_parts_and_full_values(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "technical.md").write_text(
        "update_acct_config cwLUNC-tax_zones terra1abc234def A1B2C3D4 --node",
        encoding="utf-8",
    )
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    for query in ["acct", "tax", "terra1abc234def", "A1B2C3D4", "node"]:
        assert [item.title for item in service.search(query)] == ["technical"]


def test_search_supports_accent_prefix_wildcard_fuzzy_and_phrase_queries(
    tmp_path: Path,
):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "guide.md").write_text(
        "Run terrad from the café during the bonding curve migration #chain",
        encoding="utf-8",
    )
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    assert [item.title for item in service.search("cafe")] == ["guide"]
    assert [item.title for item in service.search("terra*")] == ["guide"]
    assert [item.title for item in service.search("te?rad")] == ["guide"]
    assert [item.title for item in service.search("terrd~")] == ["guide"]
    assert [item.title for item in service.search('"bonding curve"')] == [
        "guide"
    ]
    assert [item.title for item in service.search("tags:chain")] == ["guide"]
    assert service.search("terr") == []


def test_title_and_tag_matches_rank_above_content_only_matches(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "needle.md").write_text("other text", encoding="utf-8")
    (root / "tag.md").write_text("#needle", encoding="utf-8")
    (root / "content.md").write_text("needle", encoding="utf-8")
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    assert [item.title for item in service.search("needle")] == [
        "tag",
        "needle",
        "content",
    ]
    assert [item.title for item in service.search("title:needle")] == [
        "needle"
    ]
