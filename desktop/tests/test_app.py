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


def test_startup_trace_records_timed_events(tmp_path: Path):
    from flatnotes_desktop.startup import StartupTrace

    times = iter((100.0, 101.25))
    trace = StartupTrace(tmp_path / "startup.log", clock=lambda: next(times))

    trace("frontend-mounted")

    content = (tmp_path / "startup.log").read_text(encoding="utf-8")
    assert "+1.250s" in content
    assert "frontend-mounted" in content


def test_dom_binding_waits_for_window_loaded():
    from flatnotes_desktop.app import bind_after_window_loaded

    events = []

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            self.target()

    class Loaded:
        def wait(self):
            events.append("waited")

    class Window:
        events = type("Events", (), {"loaded": Loaded()})()

    bind_after_window_loaded(Window(), lambda _window: events.append("bound"), events.append, thread_factory=FakeThread)

    assert events == ["waiting-for-window-loaded", "waited", "bound"]
