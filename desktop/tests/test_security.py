from pathlib import Path

import pytest


def test_workspace_path_rejects_symlink_escape(tmp_path: Path):
    from flatnotes_desktop.paths import workspace_note_path

    root = tmp_path / "notes"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    link = root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(ValueError, match="workspace"):
        workspace_note_path(root, "linked/escape")


def test_workspace_path_rejects_absolute_title(tmp_path: Path):
    from flatnotes_desktop.paths import workspace_note_path

    root = tmp_path / "notes"
    root.mkdir()
    with pytest.raises(ValueError, match="workspace"):
        workspace_note_path(root, "/outside")
