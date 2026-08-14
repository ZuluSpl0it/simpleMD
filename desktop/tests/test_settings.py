import json


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


def test_settings_default_heading_colors(tmp_path):
    from flatnotes_desktop.models import default_heading_colors
    from flatnotes_desktop.settings import SettingsStore

    settings = SettingsStore(tmp_path / "data").load()

    assert settings.heading_colors == default_heading_colors()


def test_settings_validate_and_preserve_heading_colors(tmp_path):
    from flatnotes_desktop.models import default_heading_colors
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        json.dumps(
            {
                "heading_colors": {
                    "dark": {
                        "h1": "#abcdef",
                        "h2": "#12345",
                        "h3": 123456,
                    },
                    "light": {"h6": "#1020A0"},
                }
            }
        ),
        encoding="utf-8",
    )

    defaults = default_heading_colors()
    settings = store.load()

    assert settings.heading_colors["dark"]["h1"] == "#abcdef"
    assert settings.heading_colors["dark"]["h2"] == defaults["dark"]["h2"]
    assert settings.heading_colors["dark"]["h3"] == defaults["dark"]["h3"]
    assert settings.heading_colors["light"]["h6"] == "#1020A0"

    store.save_theme("light")
    store.save_workspace(r"D:\\Notes")

    saved = json.loads(store.path.read_text(encoding="utf-8"))
    assert saved["heading_colors"] == settings.heading_colors
