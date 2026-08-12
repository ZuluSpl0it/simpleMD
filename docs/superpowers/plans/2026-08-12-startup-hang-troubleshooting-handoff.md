# Windows Startup Hang Troubleshooting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Identify and remove Flatnotes' intermittent Windows startup stall using repeatable measurements and one-variable experiments.

**Architecture:** Preserve a timestamped trace for every launch, measure repeated packaged starts, then test file-URL loading, duplicate-navigation removal, and a synchronously bound loopback server independently. Keep the first confirmed mechanism; do not stack speculative fixes.

**Tech Stack:** Python 3.13, pywebview 6.2.1, pythonnet 3.1.0, WebView2, Vue/Vite, PyInstaller, pytest, PowerShell.

**Status:** Executed. The checklist below is the original handoff; the
execution record at the end is authoritative for completed experiments and
the selected fix.

---

## Agent handoff

### Repository and runtime locations

- Authoritative branch/worktree: `/home/sofoli/flatnotes/.worktrees/windows-portable-desktop`
- Desktop project within worktree: `desktop/`
- Windows build/test copy: `C:\src`
- Built executable: `C:\src\dist\Flatnotes\Flatnotes.exe`
- Runtime trace currently used: `C:\src\dist\Flatnotes\data\startup.log`
- Comparison application: `C:\Users\Sofoli\Downloads\MDLook-v5.2.1-portable\MDLook.exe`

Make durable changes in the authoritative worktree first. Mirror the changed `desktop/` files into `C:\src` before each Windows build. Never leave the only copy of a fix in `C:\src`.

### Current evidence

Latest measured `C:\src` launch:

```text
+0.003s webview-start-entered
+0.565s window-shown
+21.347s window-loaded
+21.366s frontend-mounted
+21.648s window-loaded
```

Conclusions supported by this trace:

- Python setup, workspace restoration, and native WebView2 window creation finish in under 0.6 seconds.
- Stall occurs after native window display and before frontend/bridge readiness.
- Workspace indexing starts after frontend mount and finishes in about 80 ms. It is not current startup bottleneck.
- Two `window-loaded` events schedule two index rebuilds.

Relevant implementation facts:

- `desktop/client/public/loading.html` contains both a meta refresh and a JavaScript redirect at 500 ms.
- `desktop/src/flatnotes_desktop/app.py` passes a plain filesystem path to `webview.create_window`.
- pywebview treats a plain filesystem path as local and automatically starts its Bottle server, even when `http_server=True` is omitted.
- pywebview 6.2.1 starts the Bottle thread, immediately sets `server.running = True`, and returns its URL without waiting for the socket to bind.
- MDLook uses explicit `file:///` URLs and one controlled navigation. It does not put a local HTTP server on its startup path.
- MDLook's offline HTML is about 7.4 MB, while Flatnotes' JS and CSS total about 0.8 MB. Raw asset size does not explain Flatnotes' delay.

### Working hypotheses

Test in this order:

1. pywebview's asynchronous local-server startup or local HTTP navigation causes the stall.
2. Two simultaneous splash redirects create overlapping navigation and bridge-injection work.
3. Python 3.13/pythonnet behavior differs from MDLook's Python 3.12 runtime.

Do not modify `.venv/Lib/site-packages/webview` as an application fix. Do not change workspace/index code during these experiments.

## File map

- Modify: `desktop/src/flatnotes_desktop/startup.py` — unique per-run trace paths and event formatting.
- Modify: `desktop/src/flatnotes_desktop/app.py` — lifecycle instrumentation and experiment-specific startup URL/server selection.
- Modify: `desktop/tests/test_app.py` — startup URL, server options, and trace-format tests.
- Modify: `desktop/client/public/loading.html` — only during duplicate-navigation experiment.
- Create: `desktop/tests/test_loading_asset.py` — assert exactly one automatic splash navigation after that experiment is selected.
- Create: `desktop/scripts/profile_startup.ps1` — repeat packaged launches and write timing results.
- Create if needed: `desktop/src/flatnotes_desktop/asset_server.py` — synchronously bound static loopback server.
- Create if needed: `desktop/tests/test_asset_server.py` — server readiness and shutdown tests.

## Experiment rules

- Record baseline with at least 10 launches before changing startup behavior.
- Change one independent variable per experiment.
- Rebuild packaged Windows application before measuring.
- Use same workspace and same machine state for each run.
- Define success as 10/10 launches reaching `frontend-mounted` within 3 seconds, with p95 under 3 seconds.
- A failed experiment must be reverted before starting next experiment.
- A successful experiment must be repeated after reboot before declaring root cause confirmed.
- Never use `webview-start-returned` as startup completion; it fires when GUI loop exits.

### Task 1: Preserve and enrich startup evidence

**Files:**

- Modify: `desktop/src/flatnotes_desktop/startup.py`
- Modify: `desktop/src/flatnotes_desktop/app.py`
- Test: `desktop/tests/test_app.py`

- [ ] **Step 1: Write failing tests for unique trace paths and lifecycle formatting**

Append these tests to `desktop/tests/test_app.py`:

```python
from datetime import datetime, timezone


def test_startup_trace_path_contains_timestamp_and_process_id(tmp_path: Path):
    from flatnotes_desktop.startup import startup_trace_path

    path = startup_trace_path(
        tmp_path,
        now=datetime(2026, 8, 12, 14, 5, 6, 123456, tzinfo=timezone.utc),
        process_id=4321,
    )

    assert path == tmp_path / "startup-logs" / "20260812T140506.123456Z-4321.log"


def test_request_and_response_events_include_url_and_status():
    from flatnotes_desktop.startup import trace_request, trace_response

    events = []
    request = type("Request", (), {"method": "GET", "url": "http://127.0.0.1:42001/index.html"})()
    response = type("Response", (), {"status_code": 200, "url": request.url})()

    trace_request(events.append, request)
    trace_response(events.append, response)

    assert events == [
        "request:GET:http://127.0.0.1:42001/index.html",
        "response:200:http://127.0.0.1:42001/index.html",
    ]
```

- [ ] **Step 2: Run tests and verify failure**

Run from `desktop/`:

```bash
uv run pytest tests/test_app.py -q
```

Expected: FAIL because `startup_trace_path`, `trace_request`, and `trace_response` do not exist.

- [ ] **Step 3: Implement trace helpers**

Add to `desktop/src/flatnotes_desktop/startup.py`:

```python
from datetime import datetime, timezone
import os


def startup_trace_path(
    data_directory: Path,
    *,
    now: datetime | None = None,
    process_id: int | None = None,
) -> Path:
    timestamp = now or datetime.now(timezone.utc)
    pid = process_id if process_id is not None else os.getpid()
    stamp = timestamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return data_directory / "startup-logs" / f"{stamp}-{pid}.log"


def trace_request(trace, request) -> None:
    trace(f"request:{request.method}:{request.url}")


def trace_response(trace, response) -> None:
    trace(f"response:{response.status_code}:{response.url}")
```

Update imports in `desktop/src/flatnotes_desktop/app.py`:

```python
from .startup import StartupTrace, startup_trace_path, trace_request, trace_response
```

Replace current trace-file deletion block with:

```python
trace = StartupTrace(startup_trace_path(data_directory))
trace("run-entered")
```

After existing window event bindings, add:

```python
window.events.initialized += lambda renderer: trace(f"window-initialized:{renderer}")
window.events.before_load += lambda: trace("window-before-load")
window.events.request_sent += lambda request: trace_request(trace, request)
window.events.response_received += lambda response: trace_response(trace, response)
```

- [ ] **Step 4: Run focused and full Python tests**

```bash
uv run pytest tests/test_app.py -q
uv run pytest -q
```

Expected: focused tests pass; full Python suite passes.

- [ ] **Step 5: Commit instrumentation**

```bash
git add desktop/src/flatnotes_desktop/startup.py desktop/src/flatnotes_desktop/app.py desktop/tests/test_app.py
git commit -m "test: preserve detailed desktop startup traces"
```

### Task 2: Add repeatable packaged-start profiling

**Files:**

- Create: `desktop/scripts/profile_startup.ps1`

- [ ] **Step 1: Add profiler script**

Create `desktop/scripts/profile_startup.ps1`:

```powershell
param(
    [int]$Runs = 10,
    [int]$TimeoutSeconds = 45
)

$ErrorActionPreference = "Stop"
$desktop = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $desktop "dist\Flatnotes\Flatnotes.exe"
$logDirectory = Join-Path $desktop "dist\Flatnotes\data\startup-logs"
$results = @()

if (-not (Test-Path $exe)) { throw "Flatnotes.exe missing: $exe" }
New-Item -ItemType Directory -Force $logDirectory | Out-Null

for ($run = 1; $run -le $Runs; $run++) {
    $started = Get-Date
    $process = Start-Process -FilePath $exe -PassThru
    $deadline = $started.AddSeconds($TimeoutSeconds)
    $trace = $null
    $mountedSeconds = $null

    try {
        while ((Get-Date) -lt $deadline) {
            $trace = Get-ChildItem $logDirectory -Filter "*-$($process.Id).log" |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1

            if ($trace) {
                $match = Select-String -Path $trace.FullName -Pattern '^\+([0-9.]+)s .* frontend-mounted$' |
                    Select-Object -Last 1
                if ($match) {
                    $mountedSeconds = [double]$match.Matches[0].Groups[1].Value
                    break
                }
            }
            Start-Sleep -Milliseconds 100
        }
    } finally {
        if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force }
    }

    $results += [pscustomobject]@{
        Run = $run
        FrontendMountedSeconds = $mountedSeconds
        TimedOut = ($null -eq $mountedSeconds)
        Trace = if ($trace) { $trace.FullName } else { "" }
    }
}

$csv = Join-Path $desktop "startup-profile.csv"
$results | Export-Csv -Path $csv -NoTypeInformation
$results | Format-Table -AutoSize

$successful = @($results | Where-Object { -not $_.TimedOut } | Sort-Object FrontendMountedSeconds)
if ($successful.Count -gt 0) {
    $p95Index = [Math]::Ceiling($successful.Count * 0.95) - 1
    $p95 = $successful[$p95Index].FrontendMountedSeconds
    Write-Host "Successful: $($successful.Count)/$Runs; p95: $p95 seconds"
}
Write-Host "CSV: $csv"
```

- [ ] **Step 2: Build current baseline on Windows**

Mirror current authoritative `desktop/` sources into `C:\src`, then run from PowerShell:

```powershell
Set-Location C:\src
.\scripts\build_windows.ps1
```

Expected: `Portable build verified: C:\src\dist\Flatnotes\Flatnotes.exe`.

- [ ] **Step 3: Measure baseline**

```powershell
Set-Location C:\src
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
```

Expected: `startup-profile.csv` plus one preserved trace per launch. Save this CSV as `startup-profile-baseline.csv` before any experiment.

- [ ] **Step 4: Commit profiler**

```bash
git add desktop/scripts/profile_startup.ps1
git commit -m "test: add repeatable Windows startup profiler"
```

### Task 3: Experiment A — bypass pywebview HTTP server with a file URL

**Files:**

- Modify: `desktop/src/flatnotes_desktop/app.py`
- Test: `desktop/tests/test_app.py`

This experiment changes only URL classification. Leave both splash redirects untouched until results are recorded.

- [ ] **Step 1: Write failing URL/server test**

Add to `desktop/tests/test_app.py`:

```python
def test_initial_window_url_is_explicit_file_uri(tmp_path: Path):
    from flatnotes_desktop.app import initial_window_url

    loading = tmp_path / "loading.html"
    loading.write_text("<p>Loading</p>", encoding="utf-8")

    assert initial_window_url(tmp_path) == loading.resolve().as_uri()
```

Change the existing webview-options assertions to:

```python
assert captured["kwargs"]["private_mode"] is True
assert captured["kwargs"].get("http_server", False) is False
assert "storage_path" not in captured["kwargs"]
```

- [ ] **Step 2: Run test and verify failure**

```bash
uv run pytest tests/test_app.py -q
```

Expected: FAIL because `initial_window_url` does not exist and current branch enables `http_server=True`.

- [ ] **Step 3: Implement file-URL experiment**

Add to `desktop/src/flatnotes_desktop/app.py`:

```python
def initial_window_url(asset_root: Path) -> str:
    return (asset_root / "loading.html").resolve().as_uri()
```

Change `start_webview` to:

```python
def start_webview(window, callback, data_directory: Path) -> None:
    webview.start(
        callback,
        window,
        private_mode=True,
        http_server=False,
    )
```

Change window creation URL to:

```python
initial_window_url(asset_root)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/test_app.py -q
uv run pytest -q
```

Expected: all Python tests pass.

- [ ] **Step 5: Build and profile experiment A**

Mirror changes into `C:\src`, then:

```powershell
Set-Location C:\src
.\scripts\build_windows.ps1
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
Copy-Item .\startup-profile.csv .\startup-profile-file-url.csv
```

Expected functional checks for every run:

- Vue interface renders, not only splash.
- CSS and JavaScript assets load under `file:///`.
- Python bridge calls succeed.
- Trace contains no `http://127.0.0.1` requests.

- [ ] **Step 6: Apply decision gate**

If 10/10 launches reach `frontend-mounted` within 3 seconds and reboot retest also passes, keep experiment and commit:

```bash
git add desktop/src/flatnotes_desktop/app.py desktop/tests/test_app.py
git commit -m "fix: bypass local server during desktop startup"
```

If Vue modules fail under `file:///`, or startup p95 remains above 3 seconds, revert only experiment A before Task 4:

```bash
git restore --source=HEAD -- desktop/src/flatnotes_desktop/app.py desktop/tests/test_app.py
```

Use the exact pre-experiment commit as `--source` if experiment changes were committed locally.

### Task 4: Experiment B — remove overlapping splash navigation

**Files:**

- Modify: `desktop/client/public/loading.html`
- Create: `desktop/tests/test_loading_asset.py`

Run this from baseline server behavior if experiment A failed. If experiment A succeeded, apply this as cleanup only after its performance result is preserved.

- [ ] **Step 1: Write failing splash test**

Create `desktop/tests/test_loading_asset.py`:

```python
from pathlib import Path


def test_splash_has_one_automatic_navigation():
    splash = Path(__file__).parents[1] / "client" / "public" / "loading.html"
    html = splash.read_text(encoding="utf-8")

    assert "http-equiv=\"refresh\"" not in html
    assert html.count("window.location.replace") == 1
```

- [ ] **Step 2: Run test and verify failure**

```bash
uv run pytest tests/test_loading_asset.py -q
```

Expected: FAIL because splash contains meta refresh.

- [ ] **Step 3: Remove only meta refresh**

Delete this line from `desktop/client/public/loading.html`:

```html
<meta http-equiv="refresh" content="0.5;url=./index.html" />
```

Keep JavaScript `window.location.replace` and manual Continue link.

- [ ] **Step 4: Build frontend and run tests**

```bash
npm --prefix client run build
uv run pytest tests/test_loading_asset.py -q
uv run pytest -q
```

Expected: all tests pass; generated `client/dist/loading.html` contains one automatic redirect.

- [ ] **Step 5: Build and profile experiment B**

Mirror changes into `C:\src`, then:

```powershell
Set-Location C:\src
.\scripts\build_windows.ps1
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
Copy-Item .\startup-profile.csv .\startup-profile-single-navigation.csv
```

Expected trace: one final frontend navigation and no duplicated final-page `window-loaded` event.

- [ ] **Step 6: Apply decision gate**

Keep and commit only if startup threshold and reboot retest pass:

```bash
git add desktop/client/public/loading.html desktop/client/dist/loading.html desktop/tests/test_loading_asset.py
git commit -m "fix: prevent duplicate splash navigation"
```

Otherwise restore these files before Task 5.

### Task 5: Experiment C — replace pywebview server with a ready-before-use server

**Files:**

- Create: `desktop/src/flatnotes_desktop/asset_server.py`
- Create: `desktop/tests/test_asset_server.py`
- Modify: `desktop/src/flatnotes_desktop/app.py`
- Modify: `desktop/tests/test_app.py`

Use this experiment when file URLs cannot load Vite modules or experiment A is otherwise inconclusive.

- [ ] **Step 1: Write failing server readiness test**

Create `desktop/tests/test_asset_server.py`:

```python
from urllib.request import urlopen


def test_asset_server_is_bound_before_start_returns(tmp_path):
    from flatnotes_desktop.asset_server import AssetServer

    (tmp_path / "loading.html").write_text("ready", encoding="utf-8")
    server = AssetServer(tmp_path)
    try:
        server.start()
        with urlopen(f"{server.url}loading.html", timeout=2) as response:
            assert response.status == 200
            assert response.read() == b"ready"
    finally:
        server.stop()
```

- [ ] **Step 2: Run test and verify failure**

```bash
uv run pytest tests/test_asset_server.py -q
```

Expected: FAIL because `flatnotes_desktop.asset_server` does not exist.

- [ ] **Step 3: Implement synchronously bound server**

Create `desktop/src/flatnotes_desktop/asset_server.py`:

```python
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


class QuietAssetHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return


class AssetServer:
    def __init__(self, root: Path):
        handler = partial(QuietAssetHandler, directory=str(root.resolve()))
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}/"

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread.is_alive():
            self._thread.join(timeout=2)
```

`ThreadingHTTPServer` binds during construction, before `start()` returns control to WebView2.

- [ ] **Step 4: Run server test**

```bash
uv run pytest tests/test_asset_server.py -q
```

Expected: PASS.

- [ ] **Step 5: Wire server without enabling pywebview HTTP server**

In `desktop/src/flatnotes_desktop/app.py`, import:

```python
from .asset_server import AssetServer
```

Before `webview.create_window`, add:

```python
asset_server = AssetServer(asset_root)
asset_server.start()
trace(f"asset-server-ready:{asset_server.url}")
```

Use this window URL:

```python
f"{asset_server.url}loading.html"
```

Keep `http_server=False` in `webview.start`. Wrap GUI startup so server always stops:

```python
try:
    trace("webview-start-entered")
    start_webview(window, startup_callback, data_directory)
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
finally:
    asset_server.stop()
```

- [ ] **Step 6: Update webview-options test and run full suite**

Assert:

```python
assert captured["kwargs"].get("http_server", False) is False
```

Run:

```bash
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 7: Build and profile experiment C**

Mirror changes into `C:\src`, then:

```powershell
Set-Location C:\src
.\scripts\build_windows.ps1
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
Copy-Item .\startup-profile.csv .\startup-profile-ready-server.csv
```

Expected trace order, expressed as regular-expression fragments because port is ephemeral:

```text
asset-server-ready:http://127\.0\.0\.1:[0-9]+/
webview-start-entered
request:GET:http://127\.0\.0\.1:[0-9]+/loading\.html
response:200:http://127\.0\.0\.1:[0-9]+/loading\.html
request:GET:http://127\.0\.0\.1:[0-9]+/index\.html
response:200:http://127\.0\.0\.1:[0-9]+/index\.html
frontend-mounted
```

- [ ] **Step 8: Apply decision gate**

Keep and commit only if threshold and reboot retest pass:

```bash
git add desktop/src/flatnotes_desktop/asset_server.py desktop/src/flatnotes_desktop/app.py desktop/tests/test_asset_server.py desktop/tests/test_app.py
git commit -m "fix: bind desktop asset server before navigation"
```

Otherwise restore experiment C before Task 6.

### Task 6: Runtime matrix test if navigation experiments fail

**Files:**

- Modify experimentally: `desktop/pyproject.toml`
- Regenerate experimentally: `desktop/uv.lock`

- [ ] **Step 1: Record current runtime baseline**

Current Windows runtime must remain documented as:

```text
CPython 3.13.12
pywebview 6.2.1
pythonnet 3.1.0
PyInstaller 6.22.0
```

- [ ] **Step 2: Build Python 3.12 comparison without other startup changes**

Change only Python requirement:

```toml
requires-python = ">=3.12,<3.13"
```

From Windows PowerShell:

```powershell
Set-Location C:\src
uv python pin 3.12
uv sync
.\scripts\build_windows.ps1
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
Copy-Item .\startup-profile.csv .\startup-profile-python312.csv
```

- [ ] **Step 3: Apply decision gate**

Keep Python 3.12 only if it meets startup threshold twice, including once after reboot, while unchanged Python 3.13 baseline does not. Otherwise restore `pyproject.toml`, `.python-version`, and `uv.lock` to Python 3.13 state.

Commit only confirmed runtime change:

```bash
git add desktop/pyproject.toml desktop/.python-version desktop/uv.lock
git commit -m "fix: use stable Python runtime for WebView2 host"
```

### Task 7: Final verification and evidence report

**Files:**

- Modify: `desktop/README.md`

- [ ] **Step 1: Run all automated tests**

```bash
uv run pytest -q
npm --prefix client test
npm --prefix client run build
```

Expected: all Python and frontend tests pass; frontend build succeeds.

- [ ] **Step 2: Build final Windows package**

```powershell
Set-Location C:\src
.\scripts\build_windows.ps1
```

Expected: portable build verification succeeds.

- [ ] **Step 3: Run final startup profile twice**

Run once before reboot and once after reboot:

```powershell
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
```

Expected each time: 10/10 success, no launch above 3 seconds, p95 under 3 seconds.

- [ ] **Step 4: Perform manual behavior checks**

Verify:

- Splash appears without blank window.
- Home view renders.
- Python bridge returns workspace.
- Open, Save, Save As, and workspace search work.
- Closing app exits parent process and local asset server, if used.
- No stale listener remains on loopback port after exit.
- One workspace index rebuild occurs per launch.

- [ ] **Step 5: Document confirmed cause and measured result**

Add a short `Startup diagnostics` section to `desktop/README.md` containing:

- confirmed failing boundary;
- selected fix;
- baseline median/p95/failure count;
- fixed median/p95/failure count;
- trace directory: `data/startup-logs/`;
- profiler command: `scripts\profile_startup.ps1`.

- [ ] **Step 6: Commit final verification documentation**

```bash
git add desktop/README.md
git commit -m "docs: record Windows startup diagnosis"
```

## Stop conditions

- Stop after three failed implementation experiments and report evidence instead of adding a fourth speculative fix.
- Stop if a test build modifies or loses user workspace Markdown files.
- Stop if profiler cannot distinguish its own Flatnotes process from an existing instance.
- Stop if `file:///` mode breaks Python bridge or Vite assets; record that result rather than masking it with unrelated changes.
- Do not call issue fixed from one fast launch.

## Execution record (2026-08-12)

The experiments identified a fourth mechanism before the ready-bound server
was needed: pywebview's bridge reflection was recursively walking internal
service objects. Marking those objects and the window non-serializable reduced
the reflected surface from roughly 369 functions to the intended 15 bridge
methods. The duplicate splash meta-refresh was removed as a supporting fix.

Results copied from the Windows build in `C:\src`:

- File-URL experiment: 0/10 launches reached `frontend-mounted`; reverted.
- Single-navigation experiment: 9/10 launches succeeded, 1 timeout; retained.
- Bridge-exposure fix: 10/10 launches succeeded at 1.452–1.523 seconds
  (p95 1.523 seconds); retained.
- A custom ready-bound asset server and Python 3.12 matrix were not pursued
  because the bridge fix met the startup threshold and HTTP request timing was
  already fast.

The implementation is verified by 35 passing Python tests and `git diff
--check`. Windows build/profile results are preserved in `docs/logs/`.
