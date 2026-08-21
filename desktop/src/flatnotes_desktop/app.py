import json
from pathlib import Path
import sys
from threading import Timer

import webview
from webview.dom import DOMEventHandler

from .bridge import DesktopBridge
from .files import FileService
from .settings import SettingsStore
from .startup import StartupTrace, launch_markdown_paths, prune_startup_logs, startup_trace_path, trace_request, trace_response


def make_drop_handler(window):
    def on_drop(event):
        try:
            files = event.get("dataTransfer", {}).get("files", [])
            paths = []
            seen = set()
            for file in files:
                raw_path = file.get("pywebviewFullPath")
                if not raw_path:
                    continue
                path = Path(raw_path)
                key = str(path).casefold()
                if key in seen or path.suffix.lower() != ".md" or not path.is_file():
                    continue
                seen.add(key)
                paths.append(str(path))
            if not paths:
                return
            payload = json.dumps(paths)
            window.evaluate_js(
                "window.dispatchEvent(new CustomEvent('flatnotes-drop', "
                "{detail: {paths: " + payload + "}}));"
            )
        except (AttributeError, TypeError, ValueError, OSError):
            return

    return on_drop


def bind_drop_handlers(window):
    document = window.dom.document
    if getattr(document, "_flatnotes_drop_bound", False):
        return
    document.events.dragover += DOMEventHandler(
        lambda _event: None,
        prevent_default=True,
        stop_propagation=True,
        debounce=250,
    )
    document.events.drop += DOMEventHandler(
        make_drop_handler(window),
        prevent_default=True,
        stop_propagation=True,
    )
    document._flatnotes_drop_bound = True


def schedule_workspace_rebuild(workspace, delay: float = 2.0, timer_factory=Timer, trace=None, rebuild=None) -> None:
    """Keep Whoosh's first index build away from WebView2 initialization."""
    trace = trace or (lambda _event: None)
    rebuild_operation = rebuild or workspace.rebuild

    def rebuild():
        trace("index-rebuild-started")
        try:
            rebuild_operation()
        finally:
            trace("index-rebuild-finished")

    timer = timer_factory(delay, rebuild)
    timer.daemon = True
    timer.start()


def start_webview(window, callback, data_directory: Path) -> None:
    """Start WebView2 with native editing menus and a private profile."""
    # pywebview maps its debug flag to WebView2's default context-menu and
    # accelerator settings. Keep developer tools closed while restoring the
    # native Cut/Copy/Paste context menu.
    webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
    webview.start(
        callback,
        window,
        debug=True,
        private_mode=True,
        http_server=True,
    )


def run(arguments=None) -> None:
    launch_paths = launch_markdown_paths(sys.argv[1:] if arguments is None else arguments)
    asset_root = Path(__file__).with_name("assets")
    executable_root = Path(sys.executable).parent
    if not getattr(sys, "frozen", False):
        executable_root = Path(__file__).parents[2]
    data_directory = executable_root / "data"
    trace_path = startup_trace_path(data_directory)
    trace = StartupTrace(trace_path)
    prune_startup_logs(trace_path.parent, trace_path)
    trace("run-entered")
    bridge = DesktopBridge(
        None,
        FileService(),
        settings=SettingsStore(data_directory),
        trace=trace,
        launch_paths=launch_paths,
    )
    bridge.restore_workspace()
    trace("workspace-restored")
    window = webview.create_window(
        "simpleMD",
        str(asset_root / "loading.html"),
        js_api=bridge,
        text_select=True,
    )
    bridge.window = window
    window._serializable = False
    trace("window-configured")
    window.events.initialized += lambda renderer: trace(f"window-initialized:{renderer}")
    window.events.before_load += lambda: trace("window-before-load")
    window.events.before_show += lambda: trace("window-before-show")
    window.events.shown += lambda: trace("window-shown")
    window.events.request_sent += lambda request: trace_request(trace, request)
    window.events.response_received += lambda response: trace_response(trace, response)

    startup_rebuild_scheduled = False

    def on_loaded():
        nonlocal startup_rebuild_scheduled
        trace("window-loaded")
        bind_drop_handlers(window)
        if bridge.workspace is not None and not startup_rebuild_scheduled:
            startup_rebuild_scheduled = True
            startup_workspace = bridge.workspace
            schedule_workspace_rebuild(
                startup_workspace,
                trace=trace,
                rebuild=lambda: bridge.rebuild_workspace_if_current(startup_workspace),
            )
            trace("index-rebuild-scheduled")

    def startup_callback(_active_window):
        # Avoid pywebview's DOM event bridge during startup. On WebView2 this
        # registration can block the callback thread and leave the native
        # window showing as "Not Responding" on the first launch.
        trace("startup-callback-entered")
        trace("drop-handler-deferred")

    window.events.loaded += on_loaded

    try:
        trace("webview-start-entered")
        start_webview(window, startup_callback, data_directory)
        trace("webview-start-returned")
    except Exception as error:
        trace(f"webview-error:{type(error).__name__}")
        message = (
                "simpleMD could not start its WebView2 runtime.\n\n"
                "Install Microsoft Edge WebView2 Runtime, then start simpleMD again:\n"
            "https://developer.microsoft.com/microsoft-edge/webview2/\n\n"
            f"Details: {error}"
        )
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message, "simpleMD", 0x10)
        else:
            print(message)


if __name__ == "__main__":
    run()
