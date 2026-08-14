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


def test_settings_default_font_sizes(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    settings = SettingsStore(tmp_path / "data").load()

    assert settings.font_size == 17
    assert settings.code_font_size == 13


def test_settings_load_valid_font_sizes_and_reject_invalid_values(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"font_size": 20, "code_font_size": 15}', encoding="utf-8"
    )

    settings = store.load()

    assert settings.font_size == 20
    assert settings.code_font_size == 15

    assert store.save_theme("light").font_size == 20
    assert store.save_workspace(r"D:\\Notes").code_font_size == 15

    store.path.write_text(
        '{"font_size": 2, "code_font_size": "large"}', encoding="utf-8"
    )

    settings = store.load()

    assert settings.font_size == 17
    assert settings.code_font_size == 13
