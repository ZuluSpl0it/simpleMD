from pathlib import Path
from datetime import datetime, timezone


def test_webview_uses_private_profile(tmp_path: Path, monkeypatch):
    from flatnotes_desktop import app

    captured = {}
    monkeypatch.setattr(app.webview, "start", lambda *args, **kwargs: captured.update({"args": args, "kwargs": kwargs}))

    app.start_webview("window", "callback", tmp_path)

    assert captured["kwargs"]["private_mode"] is True
    assert captured["kwargs"]["http_server"] is True
    assert captured["kwargs"]["debug"] is True
    assert "storage_path" not in captured["kwargs"]


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


def test_delayed_index_rebuild_can_use_a_guarded_callback():
    from flatnotes_desktop.app import schedule_workspace_rebuild

    calls = []

    class FakeTimer:
        def __init__(self, delay, function):
            self.function = function
            self.daemon = False

        def start(self):
            self.function()

    schedule_workspace_rebuild(
        object(),
        timer_factory=FakeTimer,
        rebuild=lambda: calls.append("rebuilt"),
    )

    assert calls == ["rebuilt"]


def test_startup_trace_records_timed_events(tmp_path: Path):
    from flatnotes_desktop.startup import StartupTrace

    times = iter((100.0, 101.25))
    trace = StartupTrace(tmp_path / "startup.log", clock=lambda: next(times))

    trace("frontend-mounted")

    content = (tmp_path / "startup.log").read_text(encoding="utf-8")
    assert "+1.250s" in content
    assert "frontend-mounted" in content


def test_startup_trace_path_contains_timestamp_and_process_id(tmp_path: Path):
    from flatnotes_desktop.startup import startup_trace_path

    path = startup_trace_path(
        tmp_path,
        now=datetime(2026, 8, 12, 14, 5, 6, 123456, tzinfo=timezone.utc),
        process_id=4321,
    )

    assert path == tmp_path / "startup-logs" / "20260812T140506.123456Z-4321.log"


def test_request_and_response_events_include_url_and_status():
    from flatnotes_desktop.startup import trace_request, trace_response

    events = []
    request = type("Request", (), {"method": "GET", "url": "http://127.0.0.1:42001/index.html"})()
    response = type("Response", (), {"status_code": 200, "url": request.url})()

    trace_request(events.append, request)
    trace_response(events.append, response)

    assert events == [
        "request:GET:http://127.0.0.1:42001/index.html",
        "response:200:http://127.0.0.1:42001/index.html",
    ]
