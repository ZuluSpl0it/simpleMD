from pathlib import Path
import sys

import webview

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
    window = webview.create_window(
        "Flatnotes",
        str(asset_root / "index.html"),
        js_api=bridge,
    )
    bridge.window = window
    webview.start()


if __name__ == "__main__":
    run()
