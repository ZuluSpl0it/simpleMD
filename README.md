# simpleMD

simpleMD is a portable Markdown workspace and desktop editor. It stores notes
as ordinary `.md` files, provides full-text search, and supports Markdown,
WYSIWYG, and rendered reading views.

The Windows desktop app is built with Python, pywebview, and WebView2. A
workspace can be moved or selected without importing the files into a database,
so your notes remain portable and usable by other Markdown tools.

## Features

- Portable Windows desktop build (`simpleMD.exe`).
- Markdown, WYSIWYG, and read-only rendering modes.
- Full-text search across the selected workspace.
- Multiple open document tabs.
- Light and dark themes.
- Drag-and-drop opening of one or more Markdown files.
- External links open in the system browser; local Markdown links open as tabs.
- Configurable heading colors and font sizes through `data/settings.json`.
- Search indexing that can be rebuilt after files are moved or added externally.

## Windows portable app

The packaged app is self-contained. Keep the following items together:

```text
simpleMD/
├── simpleMD.exe
├── _internal/
├── data/
└── workspace/
```

The `workspace` directory is the default note location. You can choose a
different workspace from the home screen. Settings and startup diagnostics are
stored under `data/`.

To build the Windows package from a Windows checkout:

```powershell
cd desktop
./scripts/build_windows.ps1
```

The build script writes the portable package to the configured `dist`
directory and stages the frontend before invoking PyInstaller.

## Development

The web client and Python desktop shell live under `client/` and `desktop/`.
The Python services and search implementation are under `server/` and
`desktop/src/flatnotes_desktop/`.

Install the project dependencies with the package managers used by the
repository, then run the relevant test suites:

```bash
npm --prefix desktop/client test
uv run --directory desktop pytest -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development expectations.

## Relationship to Flatnotes

simpleMD is an independent application based on the work of
[Flatnotes](https://github.com/dullage/flatnotes), an MIT-licensed open-source
Markdown note-taking project by Adam Dullage. The original project provided
the web application foundation; this repository adds the simpleMD branding,
Windows desktop shell, portable packaging, startup diagnostics, and related
desktop-focused improvements.

The original MIT license and copyright notice are preserved in
[LICENSE](LICENSE). Compatibility-oriented names such as the existing
`FLATNOTES_*` environment variables and internal Python package paths are
intentionally retained for now.

## License

simpleMD is distributed under the MIT License. See [LICENSE](LICENSE).
