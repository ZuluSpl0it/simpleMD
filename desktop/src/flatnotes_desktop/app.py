import json
from pathlib import Path
import sys
from threading import Timer

import webview
from webview.dom import DOMEventHandler

from .bridge import DesktopBridge
from .files import FileService
from .settings import SettingsStore
from .startup import StartupTrace


def schedule_workspace_rebuild(workspace, delay: float = 2.0, timer_factory=Timer, trace=None) -> None:
    """Keep Whoosh's first index build away from WebView2 initialization."""
    trace = trace or (lambda _event: None)

    def rebuild():
        trace("index-rebuild-started")
        try:
            workspace.rebuild()
        finally:
            trace("index-rebuild-finished")

    timer = timer_factory(delay, rebuild)
    timer.daemon = True
    timer.start()


def start_webview(window, callback, data_directory: Path) -> None:
    """Start WebView2 with a reusable profile inside the portable data folder."""
    webview.start(
        callback,
        window,
        private_mode=False,
        storage_path=str(data_directory / "webview"),
    )


def run() -> None:
    asset_root = Path(__file__).with_name("assets")
    executable_root = Path(sys.executable).parent
    if not getattr(sys, "frozen", False):
        executable_root = Path(__file__).parents[2]
    data_directory = executable_root / "data"
    trace_path = data_directory / "startup.log"
    try:
        trace_path.unlink(missing_ok=True)
    except OSError:
        pass
    trace = StartupTrace(trace_path)
    trace("run-entered")
    bridge = DesktopBridge(
        None,
        FileService(),
        settings=SettingsStore(data_directory),
        trace=trace,
    )
    bridge.restore_workspace()
    trace("workspace-restored")
    window = webview.create_window(
        "Flatnotes",
        str(asset_root / "index.html"),
        js_api=bridge,
    )
    bridge.window = window
    trace("window-configured")
    window.events.before_show += lambda: trace("window-before-show")
    window.events.shown += lambda: trace("window-shown")
    window.events.loaded += lambda: trace("window-loaded")

    def on_drop(event):
        files = event.get("domTransfer", {}).get("files", [])
        if not files:
            return
        path = files[0].get("pywebviewFullPath")
        if path:
            payload = bridge.open_dropped_path(path)
            window.evaluate_js(
                "window.dispatchEvent(new CustomEvent('flatnotes-drop', "
                f"{{detail: {json.dumps(payload)}}}))"
            )

    def bind_dom_events(active_window):
        trace("startup-callback-entered")
        active_window.dom.document.events.drop += DOMEventHandler(
            on_drop, prevent_default=True, stop_propagation=True
        )
        trace("drop-handler-bound")
        if bridge.workspace is not None:
            schedule_workspace_rebuild(bridge.workspace, trace=trace)
            trace("index-rebuild-scheduled")

    try:
        trace("webview-start-entered")
        start_webview(window, bind_dom_events, data_directory)
        trace("webview-start-returned")
    except Exception as error:
        trace(f"webview-error:{type(error).__name__}")
        message = (
            "Flatnotes could not start its WebView2 runtime.\n\n"
            "Install Microsoft Edge WebView2 Runtime, then start Flatnotes again:\n"
            "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
            f"Details: {error}"
        )
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "Flatnotes", 0x10)
        else:
            print(message)


if __name__ == "__main__":
    run()
