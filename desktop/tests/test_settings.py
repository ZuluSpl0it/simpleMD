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
    from flatnotes_desktop.models import default_font_sizes
    from flatnotes_desktop.settings import SettingsStore

    assert SettingsStore(tmp_path / "data").load().font_size == default_font_sizes()


def test_settings_validates_font_size_entries_independently(tmp_path):
    from flatnotes_desktop.models import default_font_sizes
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"font_size":{"text":18,"code":"large",'
        '"heading_multiplier":{"h1":2.5,"h2":0,"h3":"large"}}}',
        encoding="utf-8",
    )

    defaults = default_font_sizes()
    sizes = store.load().font_size

    assert sizes["text"] == 18
    assert sizes["code"] == defaults["code"]
    assert sizes["heading_multiplier"]["h1"] == 2.5
    assert sizes["heading_multiplier"]["h2"] == defaults["heading_multiplier"]["h2"]
    assert sizes["heading_multiplier"]["h3"] == defaults["heading_multiplier"]["h3"]


def test_legacy_font_sizes_are_preserved_and_migrated_on_save(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"font_size":17,"code_font_size":13}', encoding="utf-8"
    )

    sizes = store.load().font_size
    assert sizes == {
        "text": 17,
        "code": 13,
        "heading_multiplier": {
            "h1": 2.0,
            "h2": 1.7059,
            "h3": 1.4706,
            "h4": 1.2353,
            "h5": 1.0588,
            "h6": 0.9412,
        },
    }

    store.save_theme("light")
    saved = json.loads(store.path.read_text(encoding="utf-8"))
    assert saved["font_size"] == sizes
    assert "code_font_size" not in saved


def test_legacy_font_size_34_is_preserved_as_text_size(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text('{"font_size":34}', encoding="utf-8")

    assert store.load().font_size["text"] == 34


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
