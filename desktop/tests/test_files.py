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


def test_external_open_rejects_non_markdown(tmp_path: Path):
    from flatnotes_desktop.files import FileService

    with pytest.raises(ValueError, match=".md"):
        FileService().open_external(tmp_path / "note.txt")
