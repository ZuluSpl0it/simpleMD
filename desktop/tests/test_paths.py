from pathlib import Path

import pytest


def test_workspace_path_rejects_escape(tmp_path: Path):
    from flatnotes_desktop.paths import workspace_note_path

    root = tmp_path / "notes"
    root.mkdir()

    with pytest.raises(ValueError, match="workspace"):
        workspace_note_path(root, "../outside")


def test_workspace_path_allows_nested_markdown(tmp_path: Path):
    from flatnotes_desktop.paths import workspace_note_path

    root = tmp_path / "notes"
    root.mkdir()

    assert workspace_note_path(root, "Projects/alpha/plan") == (
        root / "Projects" / "alpha" / "plan.md"
    )
