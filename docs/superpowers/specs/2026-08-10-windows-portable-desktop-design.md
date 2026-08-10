# Windows Portable Desktop Flatnotes

## Goal

Create a Windows 10/11 x64 portable desktop edition of Flatnotes. It runs without installation, opens in a native webview window, stores normal Markdown files in user-selected Windows folders, and provides fast recursive full-text search.

## Scope

- Windows x64 executable built with PyInstaller.
- Native `pywebview` host and a Vue user interface.
- Whoosh-backed recursive workspace search.
- TOAST UI Markdown and WYSIWYG editor.
- Nested workspace paths using forward-slash note titles.
- Session-only tabs for workspace and external Markdown files.
- Native folder/file dialogs and Markdown drag-and-drop opening.
- File-change detection with explicit conflict resolution.
- No login, authentication, REST API, localhost listener, installer, registry settings, or AppData requirement.

## Distribution and storage

The release is a portable folder containing `Flatnotes.exe` and a writable `data/` directory beside it. The system WebView2 Runtime renders the UI. If unavailable, the application shows an actionable message with the official runtime-install link; it does not bundle the roughly 250 MB fixed runtime.

`data/settings.json` stores the selected workspace path and window preferences. `data/index/` stores the Whoosh index. Both are portable with the application folder.

The workspace is any user-selected Windows folder. Markdown notes remain ordinary `.md` files. Workspace notes may live at any depth and are indexed recursively. An external file opened outside the workspace remains external and is never included in workspace search.

## Architecture

```text
Flatnotes.exe
├── Python host
│   ├── pywebview window, native dialogs, and drop events
│   ├── portable settings service
│   ├── local file service
│   ├── workspace/index service (Whoosh)
│   └── file-watch and conflict service
└── Vue application
    ├── Home and workspace search
    ├── session tab manager
    ├── TOAST UI Markdown editor/viewer
    └── native-action and conflict dialogs
```

Vue calls Python through a pywebview asynchronous bridge. The desktop edition does not retain FastAPI, its HTTP API, server routing, authentication, cookies, or network listener. It may reuse the existing project's TOAST UI integration, styling, and selected presentation components, but the desktop state model is new.

## Files and safety

All workspace operations resolve paths against the selected workspace root. The service rejects absolute titles, `..` traversal, invalid Windows path characters, and paths that resolve through a symbolic link or junction outside the workspace. Workspace note identifiers use `/` separators and always map to `.md` files beneath the root.

External operations use only canonical absolute paths returned by Windows file dialogs or a verified window drop event. Save As lets the user choose any `.md` destination. Saving into the workspace converts the tab into a workspace tab and makes it eligible for indexing.

## Tabs and file commands

The application starts on Home after every launch; tabs are not restored.

- **Workspace tab:** a note inside the selected workspace. Saves to its workspace path and participates in search.
- **External tab:** a file opened with File > Open or dropped on the window. Saves in place and does not participate in search.
- **New tab:** unsaved editor. Save opens a destination choice; a workspace target creates a workspace note and any other target becomes an external note.

File menu commands: New Tab, Open Markdown, Save, Save As, Select Workspace, Close Tab. Dropping a `.md` file opens it in an external tab. Dropping folders or unsupported files displays a clear error.

Closing a dirty tab or switching workspace prompts to save, discard, or cancel. Switching workspaces closes existing tabs only after all dirty-tab prompts resolve, rebuilds the index for the new workspace, then returns Home.

## External-change handling

Each opened tab records its source file timestamp and content hash when loaded or saved. A file watcher marks a tab if its backing file changes outside the app.

- Clean tab: offer Reload; never replace editor content silently.
- Dirty tab: offer Reload, Overwrite, or Save As; never overwrite silently.
- Deleted or moved backing file: keep tab content open and require Save As. Do not recreate the old path automatically.

## Search and subdirectories

Whoosh indexes workspace Markdown recursively. It preserves each note's relative path, title, content, tags, and modification time. Index synchronization detects created, modified, renamed, and deleted workspace files. Search results display relative paths and open their corresponding workspace tabs.

## Error behavior

- Missing system WebView2 Runtime: startup explanation and install link.
- Invalid/blocked workspace path: explanation, workspace unchanged.
- File I/O and watcher failures: non-destructive error dialog; preserve editor content.
- Duplicate workspace title: require a different path/title; no replacement without an explicit overwrite flow.
- Index failure: preserve files, surface error, permit retry/rebuild.

## Verification

Automated tests cover:

- Workspace containment, traversal rejection, and junction/symlink escape rejection.
- Recursive discovery and indexing of nested Markdown files.
- Workspace note create, rename, delete, search, and index rebuild.
- External Open, drag-and-drop, Save, Save As, and workspace conversion.
- Dirty tab close and workspace-switch prompts.
- External change, overwrite, reload, Save As, and deleted-file flows.
- Portable settings and index locations beside executable.

Manual Windows checks cover system WebView2 present/missing paths, x64 packaging, file dialogs, drag-and-drop, TOAST UI Markdown/WYSIWYG editing, and launch from a moved portable folder.
