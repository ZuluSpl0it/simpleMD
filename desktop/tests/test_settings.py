def test_settings_live_beside_executable(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.save_workspace(r"D:\\Notes")

    assert store.load().workspace == r"D:\\Notes"
