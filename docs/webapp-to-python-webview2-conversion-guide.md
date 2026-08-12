# Converting a Web App to a Windows Desktop App with pywebview and WebView2

This guide is a reusable starting point for turning an existing HTML/CSS/
JavaScript web app into a portable Windows desktop application. It assumes the
app has a local backend service—for example, search, filesystem access, an
index, or document conversion—and explains how to keep that service reliable
without creating slow or fragile startup behavior.

The recommended target is:

```text
Built frontend assets
        │
        ▼
WebView2 renderer ◄── pywebview desktop shell
        │                         │
        │ JS API / localhost      │ files, dialogs, lifecycle
        ▼                         ▼
Local backend service       Portable data directory
```

The backend can run in the Python process, or as a supervised Node, Go, or
Rust sidecar. Choose one boundary deliberately; avoid mixing several ad-hoc
communication mechanisms.

## 1. Decide the boundary before writing the shell

There are three practical designs.

### Design A: Python in-process service

Use pywebview's `js_api` for a small set of synchronous-looking commands that
call Python service classes. This is the simplest design when the backend is
already Python or when it needs direct access to local files.

```python
class DesktopApi:
    def __init__(self, search_service):
        self._search = search_service

    def search(self, term: str) -> list[dict]:
        return self._search.query(term)

window = webview.create_window(
    "My App",
    str(asset_root / "loading.html"),
    js_api=DesktopApi(SearchService(data_dir)),
)
webview.start(private_mode=True, http_server=True)
```

The bridge should return plain JSON-shaped values only. Keep the service
object private and mark it non-serializable when it is reachable from the API
object. pywebview exposes callable methods from `js_api`; it is not a general
object serializer or dependency-injection container. See the pywebview
[API](https://pywebview.flowrl.com/api/) and
[architecture](https://pywebview.idepy.com/en/guide/architecture) references.

Use this design when:

- the service is lightweight and local;
- Python libraries are valuable (Whoosh, filesystem tooling, scientific code);
- calls are naturally request/response shaped;
- a separate process would add more complexity than value.

### Design B: Local HTTP sidecar

Run the backend as a child process bound only to `127.0.0.1`. The frontend
talks to it over HTTP, while pywebview hosts the static frontend. The shell
must choose or receive a free port, pass a per-launch authentication token,
wait for a health endpoint, and terminate the child on exit.

```text
Python shell ──starts/supervises──► backend.exe --port 49152 --token ...
     │                              │
     └──────── WebView2 fetch ◄─────┘
```

Use this design when:

- the backend is already a standalone service;
- it has its own worker pool, runtime, or crash boundary;
- the service may later be reused by a CLI or another client;
- long-running work should not block the Python GUI host.

The HTTP sidecar must have a deterministic readiness contract:

```text
process created
→ port bound
→ /healthz returns 200
→ frontend receives base URL/token
→ UI enables backend-dependent features
```

Do not navigate the WebView2 page before the service is ready. Do not treat
“process started” or “thread created” as readiness.

### Design C: Native IPC sidecar

Named pipes or another authenticated local IPC mechanism can replace HTTP when
the service is highly sensitive or traffic is very frequent. This is more
work: define framing, request IDs, cancellation, timeouts, reconnection, and
diagnostics. Prefer Design B until a measurable requirement justifies it.

## 2. Establish the repository layout

A predictable layout makes packaging and support much easier:

```text
project/
├─ client/                    # Existing frontend source
│  ├─ src/
│  ├─ public/loading.html     # Splash copied into the production build
│  └─ dist/                   # Vite/webpack production output
├─ desktop/
│  ├─ src/app_shell/          # pywebview host and bridge
│  ├─ tests/                  # Shell/service tests
│  ├─ scripts/build_windows.ps1
│  ├─ scripts/profile_startup.ps1
│  └─ pyproject.toml
├─ sidecar/                   # Optional Node/Go/Rust backend
└─ docs/
```

Keep the authoritative source in one worktree. If Windows builds from a
mirrored directory, copy the changed source and generated frontend assets into
that directory before building. Never make a fix only in the build copy.

## 3. Build the frontend for an embedded app

The production frontend must be static and self-contained:

```powershell
npm ci
npm run test
npm run build
```

Check the generated output before packaging:

- all JavaScript and CSS references are relative or point to the intended
  local service;
- there are no development-server URLs or hot-module-reload scripts;
- the app does not assume `localhost:3000` or another fixed development port;
- assets work when the current directory is not the project root;
- the splash has exactly one automatic navigation.

### Splash-screen pattern

Use a tiny, dependency-free splash so the native window has useful content
while the renderer and bridge initialize:

```html
<main>
  <div class="spinner"></div>
  <div>Starting My App…</div>
</main>
<script>
  setTimeout(() => { window.location.replace("./index.html"); }, 500);
</script>
```

Use one redirect mechanism only. Do not combine a meta refresh, JavaScript
redirect, and manual fallback link. If the backend must be ready first, have
the shell generate the final URL after the health check or let the frontend
poll a bounded readiness endpoint.

## 4. Design the pywebview shell

The shell owns process lifecycle, paths, logging, bridge construction, window
creation, and shutdown. Keep `run()` orchestration-focused and put business
logic in testable service classes.

Recommended startup order:

1. Resolve the executable directory and writable data directory.
2. Open a unique per-process startup trace.
3. Create the backend/service objects.
4. Restore lightweight metadata only.
5. Start a sidecar and wait for health, if using one.
6. Create one WebView2 window pointed at the splash.
7. Register lightweight lifecycle/request/response events.
8. Start `webview.start(...)`.
9. Let the frontend emit an explicit `frontend-mounted` event.
10. Start indexing, watchers, and other expensive work after readiness.

The `js_api` surface should be intentionally small:

```python
class DesktopApi:
    def __init__(self, files, search):
        self._files = files
        self._search = search

    def open_document(self, path: str) -> dict:
        document = self._files.open(path)
        return {
            "path": str(document.path),
            "content": document.content,
            "modified_ns": str(document.modified_ns),
        }

    def search(self, term: str) -> list[dict]:
        return self._search.query(term)
```

### Bridge rules

- Keep the API object exposed, but mark internal service objects and the window
  `_serializable = False`.
- Keep services in private attributes such as `_search`, not public state.
- Return dictionaries/lists/scalars, not model instances or `Path` objects.
- Convert nanosecond timestamps and large integers to strings when JavaScript
  number precision could be lost.
- Validate every path, command argument, and user-provided identifier.
- Add explicit timeouts and useful errors for long-running operations.
- Keep bridge methods narrow enough to test without starting WebView2.

Do not expose a service object as `api.search_service`, `api.settings`, or
`api.workspace`. pywebview may inspect reachable attributes while generating
the JavaScript API. A large recursive object graph can make the window appear
hung before the frontend is mounted.

## 5. Python backend service pattern

For an in-process backend such as search:

```python
class SearchService:
    _serializable = False

    def __init__(self, workspace_root: Path, index_dir: Path):
        self._root = workspace_root.resolve()
        self._index_dir = index_dir

    def query(self, term: str) -> list[dict]:
        # Open/read the index here; return plain dictionaries.
        return []
```

Keep first-run indexing out of WebView2 initialization. Restore the selected
workspace quickly, show the UI, then schedule indexing in a daemon thread or
timer. Guard one-time work because pywebview's `loaded` event fires again after
the splash redirects to the final page.

For CPU-heavy or blocking Python operations, use a worker thread/process and
return a job ID. Do not block the GUI callback thread while waiting for a large
scan, subprocess, or network request.

## 6. Node, Go, and Rust sidecars

All three are feasible. The pywebview shell does not care which language owns
the service; it cares about a stable executable, a readiness protocol, a
secure local endpoint, and clean shutdown.

### Node.js

Two options are common:

1. Ship a Node runtime plus the compiled server bundle and start
   `node server.js`.
2. Produce a self-contained executable with a Node bundling tool, then test it
   on a clean Windows machine.

The first option is easier to debug and usually easier to keep current; the
second can simplify distribution but adds toolchain and native-module risks.
Use `child_process` semantics in the Node service only inside the sidecar; the
Python shell should supervise the resulting process, not depend on a global
Node installation. See Node's
[`child_process`](https://nodejs.org/api/child_process.html) documentation.

Node checklist:

- build the server bundle before packaging;
- include production dependencies and native modules explicitly;
- set the sidecar working directory and environment explicitly;
- write structured logs to the app data directory;
- handle `SIGTERM`/close and stop workers before exiting;
- verify that the packaged sidecar does not start a dev server or watcher.

### Go

Go is an excellent sidecar choice when the service can be a native HTTP or IPC
binary. Build a Windows artifact in CI and ship it beside the Python host:

```powershell
$env:GOOS = "windows"
$env:GOARCH = "amd64"
go build -trimpath -ldflags "-s -w" -o dist\backend.exe .\cmd\backend
```

Go has no separate runtime to install. Still test the binary on a clean
machine, include any required DLLs, and preserve stdout/stderr in a log during
development. The `go` command's build tooling is documented in the official
[command documentation](https://go.dev/doc/cmd).

### Rust

Rust is also a strong sidecar choice for CPU-heavy, security-sensitive, or
highly concurrent services:

```powershell
cargo build --release --target x86_64-pc-windows-msvc
Copy-Item target\x86_64-pc-windows-msvc\release\backend.exe dist\
```

Choose the Windows target deliberately (`msvc` is the usual Windows desktop
choice), test on a clean machine, and account for any native DLL/runtime
dependencies. Rust has no language runtime to install, but the executable can
still depend on platform libraries. Cargo's
[`build`](https://doc.rust-lang.org/cargo/commands/cargo-build.html) command
is the relevant release step.

### Common sidecar supervisor contract

Implement this contract regardless of language:

```text
start child with an ephemeral 127.0.0.1 port
read a readiness line or poll /healthz
pass base URL and token to the frontend
record child PID and stderr path
on close/error, terminate the child and its descendants
on timeout, collect logs and show a useful error
```

On Windows, use process-group/job-object handling where available so a child
that spawns workers cannot survive the shell. Avoid fixed ports, because an
unrelated process may already own them.

## 7. Security and data handling

“Local” does not automatically mean safe. A loopback service is reachable by
other local processes, browser extensions, and malware. Apply these defaults:

- bind sidecars to `127.0.0.1`, never `0.0.0.0`;
- choose an ephemeral port;
- generate a random per-launch token;
- require the token on every sidecar request;
- reject unexpected `Origin`/host values where practical;
- do not put secrets in command-line arguments if other local users can inspect
  the process command line;
- validate and contain every filesystem path;
- never execute frontend-provided shell commands directly;
- keep settings, indexes, logs, and user content under a known writable data
  directory—not beside a read-only installed executable.

For WebView2 deployment, decide between Evergreen and Fixed Version runtime
distribution. Evergreen is normally preferred because it updates on client
machines; Fixed Version gives tighter renderer reproducibility at the cost of
shipping and updating the runtime yourself. Microsoft documents the tradeoff
in [Evergreen vs. Fixed Version](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/evergreen-vs-fixed-version)
and provides [deployment samples](https://learn.microsoft.com/en-us/microsoft-edge/webview2/samples/deployment-samples).

Always show a clear WebView2 installation error when the runtime is missing.
Do not fail with a blank or apparently hung window.

## 8. Packaging checklist

For a Python shell built with PyInstaller:

- include the frontend `dist/` assets and splash;
- include the Python backend modules and data-file templates;
- include a Node/Go/Rust sidecar binary when applicable;
- preserve the sidecar executable name and relative location;
- keep writable data outside the bundled archive;
- set the working directory explicitly;
- avoid relying on `PATH`, a global Python, Node, Go, or Rust installation;
- build on the target architecture (normally Windows x64);
- sign the shell and sidecar binaries for production distribution;
- test from a path containing spaces and from a non-project current directory;
- test with no development tools installed;
- test upgrade behavior without deleting the user's data directory.

The WebView2 Runtime itself must also be present or installed. Microsoft
supports Evergreen bootstrapper/standalone deployment and Fixed Version
deployment; select one as part of the installer design rather than treating it
as a developer-machine prerequisite.

## 9. Startup diagnostics for every new conversion

Add diagnostics before optimizing. Each launch should write a unique trace
containing at least:

```text
run-entered
backend-process-started / backend-ready
workspace-restored
window-configured
webview-start-entered
window-initialized
window-shown
request/response URL and status
splash-loaded
frontend-mounted
first-bridge-call
index-started / index-finished
webview-error or webview-start-returned
```

A minimal profiler should:

1. start the packaged executable repeatedly;
2. identify traces by process ID;
3. wait for `frontend-mounted` with a generous timeout;
4. record success/failure and elapsed time in CSV;
5. report median, p95, maximum, and timeout count;
6. repeat after a reboot before declaring startup fixed.

Use one-variable experiments. Useful switches include:

- bridge exposure on/off;
- splash redirect count;
- indexing/watchers on/off;
- in-process service vs. sidecar;
- HTTP static assets vs. file URL;
- Evergreen vs. Fixed Version WebView2 runtime.

Do not change Python runtime, bridge shape, server mode, and frontend build in
one experiment; the result will not identify a cause.

## 10. Release acceptance criteria

Before shipping a converted app, require:

- 10/10 packaged launches reach `frontend-mounted`;
- no launch exceeds the chosen startup budget (3 seconds is a useful initial
  target for a small local app);
- p95 remains within that budget after a reboot;
- sidecar health timeout produces a visible actionable error;
- closing the window terminates the shell and sidecar processes;
- no stale listener remains on the loopback port;
- bridge methods work from a clean profile and a path with spaces;
- search/index initialization does not block first paint;
- WebView2 missing-runtime handling is tested;
- logs contain enough information to distinguish renderer, bridge, backend, and
  filesystem delays.

## Do and do not summary

### Do

- Start with a splash and one navigation.
- Keep the bridge narrow and JSON-shaped.
- Defer heavy backend work until after frontend readiness.
- Supervise sidecars with explicit health checks and shutdown.
- Bind local services to loopback with per-launch authentication.
- Package every runtime and asset the app requires.
- Measure repeated packaged launches, not only development mode.

### Do not

- Do not expose nested Python service state to pywebview.
- Do not use a fixed localhost port without a collision strategy.
- Do not assume a child process is ready because it has a PID.
- Do not rely on global Node/Python/Go/Rust installations.
- Do not perform indexing, scans, or migrations before the first paint.
- Do not use `webview.start()` return as the startup metric.
- Do not ship without a missing-WebView2 error path and diagnostic logs.
