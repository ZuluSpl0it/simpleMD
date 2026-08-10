# Windows Portable Desktop Flatnotes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable Windows desktop Flatnotes application with local Markdown files, recursive Whoosh search, external-file editing, tabs, and explicit file-conflict handling.

**Architecture:** Create a new `desktop/` application without changing the existing web-server edition. Python owns native Windows integration, portable settings, safe filesystem access, Whoosh, and change detection. Vue runs inside pywebview's loopback-only static host and calls Python through `window.pywebview.api`; it owns Home, tabs, TOAST UI editor instances, and dialogs.

**Tech Stack:** Python 3.13, pywebview Edge Chromium, Whoosh, watchdog, pytest, Vue 3, Vite, TOAST UI Editor, PyInstaller, Windows 10/11 x64.

---

## File structure

```text
desktop/
├── pyproject.toml
├── src/flatnotes_desktop/
│   ├── __init__.py
│   ├── app.py                 # pywebview bootstrap and loopback-only static host
│   ├── bridge.py              # async JS API and native dialog/drop entrypoints
│   ├── models.py              # immutable file/tab/result/fingerprint dataclasses
│   ├── paths.py               # canonical workspace containment validation
│   ├── settings.py            # data/settings.json load/save
│   ├── files.py               # exact external-file reads/writes and atomic saves
│   ├── workspace.py           # recursive workspace notes plus Whoosh index
│   └── watcher.py             # watchdog events and fingerprint comparison
├── client/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/desktop.js
│       ├── stores/tabs.js
│       ├── components/TabBar.vue
│       ├── components/FileMenu.vue
│       ├── components/ConflictDialog.vue
│       ├── components/MarkdownEditor.vue
│       └── views/HomeView.vue
├── tests/
│   ├── test_paths.py
│   ├── test_settings.py
│   ├── test_files.py
│   ├── test_workspace.py
│   ├── test_watcher.py
│   └── test_bridge.py
├── scripts/build_windows.ps1
└── flatnotes_desktop.spec
```

`desktop/client/dist/` is generated and copied into the PyInstaller bundle; never hand-edit it. The existing `client/` and `server/` remain unchanged until the desktop release has passed validation.

### Task 1: Create isolated desktop project and test harness

**Files:**
- Create: `desktop/pyproject.toml`
- Create: `desktop/src/flatnotes_desktop/__init__.py`
- Create: `desktop/tests/conftest.py`
- Create: `desktop/client/package.json`

- [ ] **Step 1: Write import test**

```python
# desktop/tests/test_smoke.py
def test_package_imports():
    import flatnotes_desktop
    assert flatnotes_desktop.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test and verify failure**

Run: `cd desktop; uv run pytest tests/test_smoke.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'flatnotes_desktop'`.

- [ ] **Step 3: Add minimal project configuration**

```toml
# desktop/pyproject.toml
[project]
name = "flatnotes-desktop"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = ["pywebview>=6,<7", "whoosh==2.7.4", "watchdog>=6,<7"]

[dependency-groups]
dev = ["pytest>=8,<9", "pyinstaller>=6,<7"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

```python
# desktop/src/flatnotes_desktop/__init__.py
__version__ = "0.1.0"
```

- [ ] **Step 4: Add frontend dependency manifest**

```json
{"private":true,"type":"module","scripts":{"build":"vite build","test":"vitest run"},"dependencies":{"@toast-ui/editor":"3.2.2","vue":"3.5.40"},"devDependencies":{"@vitejs/plugin-vue":"6.0.8","vite":"8.2.0","vitest":"4.0.18"}}
```

- [ ] **Step 5: Run test and commit**

Run: `cd desktop; uv run pytest tests/test_smoke.py -q`

Expected: `1 passed`.

```bash
git add desktop
git commit -m "feat: scaffold desktop application"
```

### Task 2: Implement portable paths, settings, and safe workspace containment

**Files:**
- Create: `desktop/src/flatnotes_desktop/models.py`
- Create: `desktop/src/flatnotes_desktop/paths.py`
- Create: `desktop/src/flatnotes_desktop/settings.py`
- Test: `desktop/tests/test_paths.py`
- Test: `desktop/tests/test_settings.py`

- [ ] **Step 1: Write failing path and settings tests**

```python
def test_workspace_path_rejects_escape(tmp_path):
    from flatnotes_desktop.paths import workspace_note_path
    root = tmp_path / "notes"; root.mkdir()
    with pytest.raises(ValueError, match="workspace"):
        workspace_note_path(root, "../outside")

def test_workspace_path_allows_nested_markdown(tmp_path):
    from flatnotes_desktop.paths import workspace_note_path
    root = tmp_path / "notes"; root.mkdir()
    assert workspace_note_path(root, "Projects/alpha/plan") == root / "Projects" / "alpha" / "plan.md"

def test_settings_live_beside_executable(tmp_path):
    from flatnotes_desktop.settings import SettingsStore
    store = SettingsStore(tmp_path / "data")
    store.save_workspace(r"D:\Notes")
    assert store.load().workspace == r"D:\Notes"
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd desktop; uv run pytest tests/test_paths.py tests/test_settings.py -q`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement canonical models and containment**

```python
@dataclass(frozen=True)
class Settings:
    workspace: str | None = None

def workspace_note_path(root: Path, title: str) -> Path:
    if not title or title.startswith(("/", "\\")) or ".." in PurePosixPath(title).parts:
        raise ValueError("note path must remain inside workspace")
    candidate = (root.resolve() / Path(*PurePosixPath(title).parts)).with_suffix(".md")
    if root.resolve() not in candidate.parents:
        raise ValueError("note path must remain inside workspace")
    return candidate
```

Use `Path.resolve(strict=False)` before every read/write. Reject `<>:"\\|?*` in each segment, empty segments, and a resolved parent outside `root.resolve()`; this covers symlink/junction escape after an existing parent is resolved. `SettingsStore` must create `data/`, write JSON atomically with `os.replace`, and return `Settings()` when file is absent.

- [ ] **Step 4: Run tests and commit**

Run: `cd desktop; uv run pytest tests/test_paths.py tests/test_settings.py -q`

Expected: all tests pass.

```bash
git add desktop/src/flatnotes_desktop/{models.py,paths.py,settings.py} desktop/tests
git commit -m "feat: add portable settings and safe workspace paths"
```

### Task 3: Build external-file service with atomic writes

**Files:**
- Create: `desktop/src/flatnotes_desktop/files.py`
- Test: `desktop/tests/test_files.py`

- [ ] **Step 1: Write failing external-file tests**

```python
def test_open_and_save_external_markdown(tmp_path):
    from flatnotes_desktop.files import FileService
    path = tmp_path / "outside.md"; path.write_text("old", encoding="utf-8")
    service = FileService()
    document = service.open_external(path)
    service.save_external(document.path, "new")
    assert path.read_text(encoding="utf-8") == "new"

def test_external_open_rejects_non_markdown(tmp_path):
    from flatnotes_desktop.files import FileService
    with pytest.raises(ValueError, match=".md"):
        FileService().open_external(tmp_path / "note.txt")
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd desktop; uv run pytest tests/test_files.py -q`

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement exact-path documents and atomic saves**

```python
def save_external(self, path: str, content: str) -> Document:
    target = self._markdown_file(path)
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(content, encoding="utf-8", newline="")
    os.replace(temporary, target)
    return self.open_external(target)
```

`_markdown_file` requires existing `.md` files for Open, accepts a `.md` destination for Save As, resolves to an absolute path, and never derives a path from a display title. Store a SHA-256 content hash and nanosecond modification time in `Document`.

- [ ] **Step 4: Run tests and commit**

Run: `cd desktop; uv run pytest tests/test_files.py -q`

Expected: all tests pass.

```bash
git add desktop/src/flatnotes_desktop/files.py desktop/tests/test_files.py
git commit -m "feat: add external markdown file service"
```

### Task 4: Add recursive workspace storage and Whoosh index

**Files:**
- Create: `desktop/src/flatnotes_desktop/workspace.py`
- Test: `desktop/tests/test_workspace.py`

- [ ] **Step 1: Write failing recursive-index tests**

```python
def test_recursive_search_keeps_relative_title(tmp_path):
    from flatnotes_desktop.workspace import WorkspaceService
    root = tmp_path / "notes"; (root / "Projects" / "alpha").mkdir(parents=True)
    (root / "Projects" / "alpha" / "plan.md").write_text("#release", encoding="utf-8")
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()
    assert [item.title for item in service.search("release")] == ["Projects/alpha/plan"]
```

- [ ] **Step 2: Run test and verify failure**

Run: `cd desktop; uv run pytest tests/test_workspace.py -q`

Expected: FAIL with missing `WorkspaceService`.

- [ ] **Step 3: Implement schema and synchronization**

```python
class WorkspaceService:
    def list_files(self) -> list[Path]:
        return sorted(path for path in self.root.rglob("*.md") if ".flatnotes" not in path.parts)

    def title_for(self, path: Path) -> str:
        return path.relative_to(self.root).with_suffix("").as_posix()
```

Create a Whoosh schema with stored `title`, `path`, `modified_ns`, content, and keyword tags. Rebuild into the portable `data/index` directory. Synchronization must delete vanished indexed paths, update a changed `modified_ns`, and add new recursively discovered files. All workspace mutations call `workspace_note_path`; create parent directories only after containment validation.

- [ ] **Step 4: Add create/rename/delete tests and run suite**

```python
def test_rename_preserves_nested_workspace_containment(tmp_path):
    service = make_workspace(tmp_path)
    service.create("A/old", "body")
    service.rename("A/old", "B/new")
    assert (tmp_path / "notes" / "B" / "new.md").exists()
    assert not (tmp_path / "notes" / "A" / "old.md").exists()
```

Run: `cd desktop; uv run pytest tests/test_workspace.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/flatnotes_desktop/workspace.py desktop/tests/test_workspace.py
git commit -m "feat: add recursive workspace search"
```

### Task 5: Detect external changes and define conflict state

**Files:**
- Create: `desktop/src/flatnotes_desktop/watcher.py`
- Modify: `desktop/src/flatnotes_desktop/models.py`
- Test: `desktop/tests/test_watcher.py`

- [ ] **Step 1: Write failing fingerprint tests**

```python
def test_changed_file_is_reported(tmp_path):
    from flatnotes_desktop.watcher import changed_since
    path = tmp_path / "note.md"; path.write_text("one")
    before = fingerprint(path)
    path.write_text("two")
    assert changed_since(path, before) is True

def test_deleted_file_is_reported(tmp_path):
    path = tmp_path / "note.md"; path.write_text("one")
    before = fingerprint(path); path.unlink()
    assert changed_since(path, before) is True
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd desktop; uv run pytest tests/test_watcher.py -q`

Expected: FAIL with missing module.

- [ ] **Step 3: Implement watcher interface**

```python
@dataclass(frozen=True)
class Fingerprint:
    modified_ns: int
    content_hash: str

class WatchService:
    def watch(self, path: Path, callback: Callable[[Path], None]) -> None: ...
    def unwatch(self, path: Path) -> None: ...
```

Use watchdog only to schedule reevaluation. `changed_since` performs final comparison of existence, `st_mtime_ns`, and SHA-256; watcher callbacks emit `{path, state: "changed" | "missing"}` to the bridge. Debounce repeated events for 250 ms. Do not write files from a watcher callback.

- [ ] **Step 4: Run tests and commit**

Run: `cd desktop; uv run pytest tests/test_watcher.py -q`

Expected: all tests pass.

```bash
git add desktop/src/flatnotes_desktop/{models.py,watcher.py} desktop/tests/test_watcher.py
git commit -m "feat: detect externally changed markdown files"
```

### Task 6: Expose services through pywebview and native Windows actions

**Files:**
- Create: `desktop/src/flatnotes_desktop/bridge.py`
- Create: `desktop/src/flatnotes_desktop/app.py`
- Test: `desktop/tests/test_bridge.py`

- [ ] **Step 1: Write failing bridge tests with a fake window**

```python
def test_open_dialog_returns_external_document(fake_window, tmp_path):
    path = tmp_path / "outside.md"; path.write_text("body")
    fake_window.dialog_result = (str(path),)
    bridge = DesktopBridge(fake_window, make_services(tmp_path))
    assert bridge.open_markdown()["kind"] == "external"
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd desktop; uv run pytest tests/test_bridge.py -q`

Expected: FAIL with missing `DesktopBridge`.

- [ ] **Step 3: Implement bridge contract**

```python
class DesktopBridge:
    def select_workspace(self) -> dict | None: ...
    def open_markdown(self) -> dict | None: ...
    def save_as(self, tab: dict) -> dict | None: ...
    def save_tab(self, tab: dict) -> dict: ...
    def search_workspace(self, term: str) -> list[dict]: ...
    def close(self) -> None: ...
```

Use `window.create_file_dialog` with `("Markdown (*.md)",)` for Open and Save As, and `webview.FOLDER_DIALOG` for Select Workspace. Return JSON-serializable documents only. Initialize pywebview with its bundled static directory and configure its server host as `127.0.0.1`; do not create FastAPI, Uvicorn, or a public route. Subscribe to pywebview's Python-side DOM drop event and read `pywebviewFullPath`; accept exactly one canonical `.md` file, then call the same external-open service.

- [ ] **Step 4: Add bridge rejection tests and run suite**

```python
def test_drop_rejects_folder_and_non_markdown(fake_window, tmp_path):
    bridge = DesktopBridge(fake_window, make_services(tmp_path))
    assert bridge.open_dropped_path(str(tmp_path)) == {"error": "Drop a Markdown file (.md)."}
```

Run: `cd desktop; uv run pytest tests/test_bridge.py -q`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/flatnotes_desktop/{app.py,bridge.py} desktop/tests/test_bridge.py
git commit -m "feat: add native desktop bridge"
```

### Task 7: Build Vue shell, bridge client, and Home search

**Files:**
- Create: `desktop/client/vite.config.js`
- Create: `desktop/client/src/main.js`
- Create: `desktop/client/src/api/desktop.js`
- Create: `desktop/client/src/App.vue`
- Create: `desktop/client/src/views/HomeView.vue`
- Test: `desktop/client/src/api/desktop.test.js`

- [ ] **Step 1: Write failing bridge-client test**

```javascript
import { describe, expect, it, vi } from "vitest";
import { searchWorkspace } from "./desktop.js";
it("calls pywebview bridge", async () => {
  window.pywebview = { api: { search_workspace: vi.fn().mockResolvedValue([]) } };
  await searchWorkspace("roadmap");
  expect(window.pywebview.api.search_workspace).toHaveBeenCalledWith("roadmap");
});
```

- [ ] **Step 2: Run test and verify failure**

Run: `cd desktop/client; npm test -- desktop.js`

Expected: FAIL because `desktop.js` does not exist.

- [ ] **Step 3: Implement bridge wrapper and Home**

```javascript
export const searchWorkspace = (term) => window.pywebview.api.search_workspace(term);
export const openMarkdown = () => window.pywebview.api.open_markdown();
```

`App.vue` renders `HomeView` by default, a persistent `TabBar`, and file menu. `HomeView` renders selected workspace status, Select Workspace action, and results returned by `searchWorkspace`. Do not add Vue Router, login components, Axios, cookies, or HTTP API calls.

- [ ] **Step 4: Run test/build and commit**

Run: `cd desktop/client; npm test -- desktop.js && npm run build`

Expected: tests pass and `dist/` is generated.

```bash
git add desktop/client
git commit -m "feat: add desktop Vue home shell"
```

### Task 8: Implement session tabs and TOAST UI editing

**Files:**
- Create: `desktop/client/src/stores/tabs.js`
- Create: `desktop/client/src/components/TabBar.vue`
- Create: `desktop/client/src/components/MarkdownEditor.vue`
- Modify: `desktop/client/src/App.vue`
- Test: `desktop/client/src/stores/tabs.test.js`

- [ ] **Step 1: Write failing tab-state tests**

```javascript
it("marks an edited tab dirty", () => {
  const tabs = createTabs();
  const id = tabs.open({ path: "C:/outside.md", kind: "external", content: "one" });
  tabs.setContent(id, "two");
  expect(tabs.byId(id).dirty).toBe(true);
});
```

- [ ] **Step 2: Run test and verify failure**

Run: `cd desktop/client; npm test -- tabs.test.js`

Expected: FAIL because `createTabs` does not exist.

- [ ] **Step 3: Implement tab domain state and editor**

```javascript
export function createTabs() {
  const items = reactive([]); const activeId = ref(null);
  function open(document) { /* create id, baseline fingerprint, dirty false */ }
  function setContent(id, content) { byId(id).content = content; byId(id).dirty = content !== byId(id).savedContent; }
  return { items, activeId, open, byId, setContent };
}
```

`MarkdownEditor.vue` creates and destroys one TOAST UI editor for active tab changes, seeds it from tab content, emits Markdown changes, and preserves existing Markdown/WYSIWYG choice per tab. Tab labels show workspace-relative title or external filename; no tab persistence is written to settings.

- [ ] **Step 4: Add close prompt test, run tests, and commit**

```javascript
it("requires resolution before closing dirty tab", () => {
  const tabs = createTabs();
  const id = tabs.open({ content: "one" }); tabs.setContent(id, "two");
  expect(tabs.requestClose(id)).toEqual({ requiresConflict: true });
});
```

Run: `cd desktop/client; npm test -- tabs.test.js`

Expected: all tests pass.

```bash
git add desktop/client/src
git commit -m "feat: add session tabs and markdown editor"
```

### Task 9: Wire saves, drag/drop notifications, and conflict dialogs

**Files:**
- Create: `desktop/client/src/components/FileMenu.vue`
- Create: `desktop/client/src/components/ConflictDialog.vue`
- Modify: `desktop/client/src/api/desktop.js`
- Modify: `desktop/client/src/App.vue`
- Test: `desktop/client/src/components/ConflictDialog.test.js`

- [ ] **Step 1: Write failing conflict-action test**

```javascript
it("offers reload, overwrite, and save-as for dirty changed tab", () => {
  const actions = conflictActions({ dirty: true, externalState: "changed" });
  expect(actions).toEqual(["reload", "overwrite", "saveAs"]);
});
```

- [ ] **Step 2: Run test and verify failure**

Run: `cd desktop/client; npm test -- ConflictDialog.test.js`

Expected: FAIL with missing component/helper.

- [ ] **Step 3: Implement explicit, non-destructive flows**

```javascript
const actions = computed(() => props.tab.dirty ? ["reload", "overwrite", "saveAs"] : ["reload"]);
async function overwrite() { await saveTab(props.tab); emit("resolved", "overwrite"); }
```

`FileMenu` invokes native New, Open, Save, Save As, Select Workspace, Close Tab commands. `App.vue` consumes bridge watcher events: clean changed tab opens Reload-only dialog; dirty changed tab opens Reload/Overwrite/Save As; missing tab opens Save As-only dialog. Python DOM drop events call `window.evaluate_js` to dispatch a `flatnotes:drop` CustomEvent; `App.vue` opens returned document in a new external tab. Never reload, overwrite, or recreate a missing file automatically.

- [ ] **Step 4: Add workspace-switch and missing-file tests**

```javascript
it("only offers save-as for missing file", () => {
  expect(conflictActions({ dirty: true, externalState: "missing" })).toEqual(["saveAs"]);
});
```

Run: `cd desktop/client; npm test && npm run build`

Expected: all frontend tests pass and production build succeeds.

- [ ] **Step 5: Commit**

```bash
git add desktop/client/src
git commit -m "feat: add file actions and conflict resolution"
```

### Task 10: Package portable Windows release and verify it

**Files:**
- Create: `desktop/flatnotes_desktop.spec`
- Create: `desktop/scripts/build_windows.ps1`
- Create: `desktop/README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Write packaging smoke check**

```powershell
$exe = Join-Path $PSScriptRoot "..\dist\Flatnotes\Flatnotes.exe"
if (-not (Test-Path $exe)) { throw "Flatnotes.exe missing" }
if (-not (Test-Path (Join-Path (Split-Path $exe) "data"))) { throw "portable data directory missing" }
```

- [ ] **Step 2: Run check and verify failure before build**

Run: `powershell -ExecutionPolicy Bypass -File desktop/scripts/build_windows.ps1 -VerifyOnly`

Expected: FAIL with `Flatnotes.exe missing`.

- [ ] **Step 3: Add deterministic build script and PyInstaller spec**

```powershell
Push-Location $PSScriptRoot\..
npm --prefix client ci
npm --prefix client run build
uv run pyinstaller flatnotes_desktop.spec --noconfirm
New-Item -ItemType Directory -Force dist\Flatnotes\data | Out-Null
Pop-Location
```

The spec includes `flatnotes_desktop`, Whoosh, watchdog, pywebview, client `dist/`, icon assets, and no WebView2 fixed runtime. `.gitignore` excludes `desktop/client/dist/`, `desktop/build/`, `desktop/dist/`, and `desktop/data/`.

- [ ] **Step 4: Build and run complete verification**

Run: `powershell -ExecutionPolicy Bypass -File desktop/scripts/build_windows.ps1`

Expected: `desktop/dist/Flatnotes/Flatnotes.exe` and an adjacent writable `data/` directory exist.

Manual Windows checklist: launch from a USB/moved folder; use installed WebView2; verify missing-runtime guidance on VM; select workspace; create/search nested note; Open and drop external `.md`; edit/save; modify file outside app; verify Reload/Overwrite/Save As; delete file outside app; verify Save As only; restart and verify Home/no restored tabs.

- [ ] **Step 5: Commit**

```bash
git add desktop .gitignore
git commit -m "build: package portable Windows desktop app"
```

## Plan self-review

- Spec coverage: Tasks 2–4 cover portable storage, safe filesystem access, nested notes, and search. Tasks 3, 5, 6, and 9 cover external files, native dialogs/drop, and conflict handling. Tasks 7–9 cover Home, session tabs, TOAST UI, and no-auth desktop UI. Task 10 covers WebView2 messaging, portable packaging, and Windows validation.
- Placeholder scan: no TBD/TODO, vague test instruction, or undeclared module remains.
- Type consistency: `Document` and `Fingerprint` originate in `models.py`; all Python bridge methods serialize dicts; Vue uses `kind`, `path`, `content`, `dirty`, and `externalState` consistently.
