from pathlib import Path


def test_splash_has_one_automatic_navigation():
    splash = Path(__file__).parents[1] / "client" / "public" / "loading.html"
    html = splash.read_text(encoding="utf-8")

    assert 'http-equiv="refresh"' not in html
    assert html.count("window.location.replace") == 1
    assert "Continue" not in html
