def test_settings_live_beside_executable(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.save_workspace(r"D:\\Notes")

    assert store.load().workspace == r"D:\\Notes"


def test_settings_persist_theme_and_default_to_dark(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")

    assert store.load().theme == "dark"
    assert store.save_theme("light").theme == "light"
    assert store.load().theme == "light"
