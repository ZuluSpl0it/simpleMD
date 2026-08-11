from pathlib import Path

import pytest


def test_open_and_save_external_markdown(tmp_path: Path):
    from flatnotes_desktop.files import FileService

    path = tmp_path / "outside.md"
    path.write_text("old", encoding="utf-8")
    service = FileService()

    document = service.open_external(path)
    saved = service.save_external(document.path, "new")

    assert path.read_text(encoding="utf-8") == "new"
    assert saved.content == "new"


def test_save_external_creates_missing_subfolders(tmp_path: Path):
    from flatnotes_desktop.files import FileService

    path = tmp_path / "Projects" / "2026" / "meeting.md"

    saved = FileService().save_external(path, "notes")

    assert path.read_text(encoding="utf-8") == "notes"
    assert saved.path == path.resolve()


def test_external_open_rejects_non_markdown(tmp_path: Path):
    from flatnotes_desktop.files import FileService

    with pytest.raises(ValueError, match=".md"):
        FileService().open_external(tmp_path / "note.txt")
