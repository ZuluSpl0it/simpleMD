from pathlib import Path


def test_changed_file_is_reported(tmp_path: Path):
    from flatnotes_desktop.watcher import changed_since, fingerprint

    path = tmp_path / "note.md"
    path.write_text("one", encoding="utf-8")
    before = fingerprint(path)
    path.write_text("two", encoding="utf-8")

    assert changed_since(path, before) is True


def test_deleted_file_is_reported(tmp_path: Path):
    from flatnotes_desktop.watcher import changed_since, fingerprint

    path = tmp_path / "note.md"
    path.write_text("one", encoding="utf-8")
    before = fingerprint(path)
    path.unlink()

    assert changed_since(path, before) is True
