from pathlib import Path


def test_webview_uses_persistent_portable_profile(tmp_path: Path, monkeypatch):
    from flatnotes_desktop import app

    captured = {}
    monkeypatch.setattr(app.webview, "start", lambda *args, **kwargs: captured.update({"args": args, "kwargs": kwargs}))

    app.start_webview("window", "callback", tmp_path)

    assert captured["kwargs"]["private_mode"] is False
    assert captured["kwargs"]["storage_path"] == str(tmp_path / "webview")


def test_index_rebuild_is_delayed_until_after_startup():
    from flatnotes_desktop.app import schedule_workspace_rebuild

    calls = []

    class FakeTimer:
        def __init__(self, delay, function):
            calls.append(("created", delay, function))
            self.daemon = False

        def start(self):
            calls.append(("started", self.daemon))

    workspace = type("Workspace", (), {"rebuild": lambda self: None})()

    schedule_workspace_rebuild(workspace, timer_factory=FakeTimer)

    assert calls[0][0:2] == ("created", 2.0)
    assert calls[1] == ("started", True)
