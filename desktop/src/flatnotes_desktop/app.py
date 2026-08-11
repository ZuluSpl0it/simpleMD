import json
from pathlib import Path
import sys
from threading import Thread

import webview
from webview.dom import DOMEventHandler

from .bridge import DesktopBridge
from .files import FileService
from .settings import SettingsStore


def run() -> None:
    asset_root = Path(__file__).with_name("assets")
    executable_root = Path(sys.executable).parent
    if not getattr(sys, "frozen", False):
        executable_root = Path(__file__).parents[2]
    bridge = DesktopBridge(
        None,
        FileService(),
        settings=SettingsStore(executable_root / "data"),
    )
    bridge.restore_workspace()
    window = webview.create_window(
        "Flatnotes",
        str(asset_root / "index.html"),
        js_api=bridge,
    )
    bridge.window = window

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
        active_window.dom.document.events.drop += DOMEventHandler(
            on_drop, prevent_default=True, stop_propagation=True
        )
        if bridge.workspace is not None:
            Thread(target=bridge.workspace.rebuild, daemon=True).start()

    try:
        webview.start(bind_dom_events, window)
    except Exception as error:
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
