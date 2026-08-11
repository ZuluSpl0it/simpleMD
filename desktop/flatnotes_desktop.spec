from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

root = Path(SPEC).parent
client_dist = root / "client" / "dist"

a = Analysis(
    [str(root / "src" / "desktop_entry.py")],
    pathex=[str(root / "src")],
    datas=[(str(client_dist), "flatnotes_desktop/assets")],
    hiddenimports=collect_submodules("flatnotes_desktop"),
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Flatnotes",
    console=False,
    upx=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="Flatnotes",
    strip=False,
    upx=False,
)
