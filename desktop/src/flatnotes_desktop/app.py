from pathlib import Path

import webview

from .bridge import DesktopBridge
from .files import FileService


def run() -> None:
    asset_root = Path(__file__).with_name("assets")
    bridge = DesktopBridge(None, FileService())
    window = webview.create_window(
        "Flatnotes",
        str(asset_root / "index.html"),
        js_api=bridge,
    )
    bridge.window = window
    webview.start()


if __name__ == "__main__":
    run()
