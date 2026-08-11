import json
from pathlib import Path
import sys

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
    bridge.load_workspace()
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

    window.dom.document.events.drop += DOMEventHandler(
        on_drop, prevent_default=True, stop_propagation=True
    )
    webview.start()


if __name__ == "__main__":
    run()
