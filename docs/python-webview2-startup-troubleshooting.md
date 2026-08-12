# Python + pywebview + WebView2 Startup Troubleshooting Guide

This guide records the startup investigation performed for Flatnotes and turns
the findings into reusable guidance for future Python desktop applications
that embed a web frontend with pywebview and Microsoft WebView2.

## Short version

The important rules are:

1. Expose a small, flat JavaScript bridge. Do not let pywebview recursively
   serialize service objects, `Path` objects, settings, windows, or other
   internal state.
2. Use one splash navigation. Do not combine an HTML meta refresh, a JavaScript
   redirect, and a manual fallback link.
3. Trace each launch with a unique file and measure a real frontend-ready
   event. `webview.start()` returning is not startup completion.
4. Keep indexing, filesystem scans, watchers, and other expensive work off the
   WebView2 initialization path.
5. Test packaged Windows launches repeatedly. One fast launch proves very
   little when the failure is intermittent.

The investigation environment was CPython 3.13.12, pywebview 6.2.1,
pythonnet 3.1.0, PyInstaller 6.22.0, and the system WebView2 Runtime. Record
these versions in future reports because renderer, Python, and pythonnet
changes can affect startup behavior.

## What caused the Flatnotes hang

The primary cause was pywebview bridge reflection. Flatnotes passed a
`DesktopBridge` instance to `js_api`. The bridge contained `FileService`,
`SettingsStore`, `WorkspaceService`, a `Path`-based data directory, and the
pywebview window. pywebview 6.2.1 walked that object graph while generating the
JavaScript API. Internal objects exposed many unintended attributes and
methods, including `Path` methods and nested service state.

The local reflection audit found approximately 369 exposed functions before
the fix and 15 intended bridge methods afterward. The fix was to mark internal
objects as non-serializable:

```python
class FileService:
    _serializable = False


class SettingsStore:
    _serializable = False


class WorkspaceService:
    _serializable = False


window._serializable = False
```

The bridge itself should expose explicit methods returning plain JSON-shaped
values (`dict`, `list`, strings, numbers, booleans, and `None`). Keep service
instances private and do not return live Python objects across the bridge.

## Secondary startup issue: overlapping splash navigation

The original splash had both of these automatic navigations:

```html
<meta http-equiv="refresh" content="0.5;url=./index.html" />
<script>setTimeout(() => { window.location.replace("./index.html"); }, 500);</script>
```

Both could fire, causing duplicate `loaded` events and overlapping bridge
injection. The final splash has one automatic redirect only:

```html
<script>
  setTimeout(() => { window.location.replace("./index.html"); }, 500);
</script>
```

Avoid a manual Continue link unless it is genuinely required. A third
navigation path makes timing and diagnostics harder to reason about. Also
remember that pywebview's `loaded` event fires for every navigation, not just
the first one. Guard one-time work explicitly:

```python
frontend_ready = False


def on_loaded():
    nonlocal frontend_ready
    if frontend_ready:
        return
    frontend_ready = True
    # One-time post-startup work here.
```

## Diagnostics performed in this investigation

### 1. Baseline trace

The original packaged build showed:

```text
+0.565s  window-shown
+21.347s window-loaded
+21.366s frontend-mounted
+21.648s window-loaded
```

Python setup, workspace restoration, and native WebView2 creation completed in
under one second. The delay was inside WebView2/frontend startup, not the
Whoosh index rebuild. The duplicate `loaded` events also confirmed that more
than one navigation was occurring.

### 2. Per-launch tracing

Each run now writes a unique trace under:

```text
data/startup-logs/YYYYMMDDTHHMMSS.ffffffZ-PID.log
```

The trace records:

- Python entry and workspace restoration;
- WebView2 initialization and window visibility;
- `before_load` and `loaded` events;
- every request URL and response status;
- frontend bridge readiness (`frontend-mounted`);
- delayed index rebuild start/finish.

This prevents one launch from overwriting the evidence from another launch.

### 3. Repeatable packaged profiling

The Windows profiler is:

```powershell
.\scripts\profile_startup.ps1 -Runs 10 -TimeoutSeconds 45
```

It starts the packaged executable, finds the trace for that process ID, waits
for `frontend-mounted`, and writes `startup-profile.csv`. Use the same machine,
workspace, build, and timeout for comparisons.

Measure `frontend-mounted`, not `webview-start-returned`: the latter occurs
when the GUI loop exits, often when the app is closing.

### 4. Controlled experiments

Only one startup variable was changed per experiment:

| Experiment | Result | Interpretation |
| --- | --- | --- |
| File URL instead of pywebview's local HTTP URL | 0/10 reached frontend readiness; scripts stalled around 20 seconds | File URLs were not a fix; reverted |
| Remove duplicate splash navigation | 9/10 succeeded; successful runs 1.753–7.843 seconds; one timeout | Necessary improvement, but not sufficient |
| Mark bridge internals non-serializable | 10/10 succeeded at 1.452–1.523 seconds; p95 1.523 seconds | Confirmed fix |

The request/response trace after the bridge fix showed local HTTP responses in
milliseconds. That ruled out the local server as the remaining bottleneck, so
a custom ready-bound server and a Python 3.12 runtime change were not added.

## pywebview and WebView2 quirks to account for

### Local files may still involve a local HTTP server

Passing a plain filesystem path to `webview.create_window` causes pywebview to
serve local assets through its Bottle server. In the Flatnotes version,
`http_server=True` is explicit. pywebview starts that server asynchronously,
so do not infer socket readiness merely from the server thread being created.

Instrument actual request/response events before replacing the server. A file
URL is not automatically faster or safer: in this investigation it failed all
10 runs because the WebView2 renderer did not complete the module load.

### Bridge reflection is startup work

The `js_api` object is inspected before the frontend can use Python methods.
Large or recursive object graphs make this phase slow and variable. The cost
can look like a frozen native window because the window is visible before the
frontend is ready.

### WebView events are not one-shot

`initialized`, `before_load`, `loaded`, and request/response events can occur on
multiple navigations. Use a one-shot guard for initialization and include the
URL in every event when diagnosing redirects.

### Startup callbacks must stay lightweight

Avoid registering drag/drop handlers, DOM callbacks, synchronous filesystem
work, or large JavaScript payloads in the first startup callback. In this app,
the DOM drop-handler registration was disabled during startup after it appeared
on the callback thread in traces. Add optional handlers after the frontend
reports ready, and keep that change separately measurable.

### Native window visibility is not frontend readiness

`window-shown` only means the native window is visible. The useful readiness
boundary is an explicit frontend event such as:

```javascript
window.pywebview.api.startup_event("frontend-mounted");
```

Use that event for profiling and user-facing readiness, not `shown` or the
return from `webview.start()`.

### Right-click menus are disabled by default

pywebview's WebView2 backend maps its `debug` flag to WebView2's
`AreDefaultContextMenusEnabled` setting. With the normal production default
(`debug=False`), text selection and Ctrl+C/Ctrl+V/Ctrl+X can work while a
right-click menu appears to do nothing.

If the app needs the native Cut/Copy/Paste menu, enable the WebView2 default
context menu but keep developer tools closed:

```python
webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
webview.start(
    callback,
    window,
    debug=True,
    private_mode=True,
    http_server=True,
)
```

This is a pywebview quirk: `debug=True` controls more than logging. Verify the
result on the target backend and pywebview version. Do not expose developer
tools accidentally; explicitly set `OPEN_DEVTOOLS_IN_DEBUG` to `False` for a
production build. `text_select=True` is a separate window option and is still
needed when the app wants users to select rendered document text.

## Startup architecture that avoids the slow path

Recommended sequence:

1. Resolve the executable/data directories.
2. Open a unique startup trace.
3. Construct the bridge with private service objects.
4. Restore workspace metadata only; do not build the search index yet.
5. Create one WebView window pointed at the splash.
6. Start WebView2 with a narrow bridge and lightweight callbacks.
7. Let the splash perform one redirect to the built frontend.
8. Have the frontend emit `frontend-mounted`.
9. Start indexing, watchers, and other expensive work after readiness, ideally
   on a daemon/background thread or timer.

The Flatnotes code delays the first index rebuild by two seconds. This keeps
Whoosh work away from WebView2 initialization, but the `loaded` handler must
still be guarded if only one rebuild is desired because it runs for each page
navigation.

## Do and do not checklist

### Do

- Use a simple HTML splash for immediate visual feedback.
- Keep exactly one automatic splash redirect.
- Add an explicit frontend-ready event and profile it.
- Use one timestamped trace per process ID.
- Include navigation URLs and response status in traces.
- Expose a small, intentionally designed bridge API.
- Mark internal service objects and the window `_serializable = False` when
  they are reachable from the bridge.
- Return plain serializable data across the bridge.
- Defer indexing, workspace scans, watchers, and thumbnail generation.
- Profile at least 10 packaged launches and repeat after a reboot for release
  confidence.
- Keep a known-good comparison build and change one variable at a time.

### Do not

- Do not expose `SettingsStore`, `Path`, `WorkspaceService`, or other mutable
  Python objects as public bridge state.
- Do not return live Python objects, file handles, threads, locks, or windows
  from bridge methods.
- Do not combine meta refresh, JavaScript redirect, and a manual fallback link.
- Do not perform a full index rebuild before the first frontend paint.
- Do not use `webview-start-returned` as the startup-success metric.
- Do not assume a `file:///` URL fixes a local-server problem without testing
  module loading under WebView2.
- Do not assume clipboard shortcuts imply that the native right-click context
  menu is enabled; configure WebView2's default context menu explicitly.
- Do not patch pywebview's installed package as the first application fix.
- Do not draw conclusions from one lucky fast launch.
- Do not treat an HTTP 200 for `loading.html` as proof that the app is ready;
  the final JavaScript bundle and bridge still need to load.

## Future regression checklist

When a new project starts slowly:

1. Capture 10 packaged launches before changing code.
2. Add unique per-run traces and request/response events.
3. Mark the exact boundaries: native window shown, splash loaded, final page
   loaded, frontend mounted, first bridge call completed.
4. Count bridge functions and inspect whether nested objects are being walked.
5. Check the splash for multiple redirects.
6. Temporarily disable indexing, watchers, drag/drop, and other startup work.
7. Run one-variable experiments and revert failed experiments.
8. Retest the selected fix after a reboot.
9. Keep the profile CSVs and representative traces with the release notes.

## Files from the Flatnotes investigation

- Startup instrumentation: `desktop/src/flatnotes_desktop/startup.py`
- WebView lifecycle and profiling hooks: `desktop/src/flatnotes_desktop/app.py`
- Bridge serialization guards: `desktop/src/flatnotes_desktop/files.py`,
  `settings.py`, and `workspace.py`
- Splash: `desktop/client/public/loading.html`
- Packaged profiler: `desktop/scripts/profile_startup.ps1`
- Automated checks: `desktop/tests/test_app.py`, `test_bridge.py`, and
  `test_loading_asset.py`
- Representative final trace:
  `docs/logs/20260812T154041.188471Z-16996.log`
- Final 10-run profile: `docs/logs/startup-profile-bridge-exposure.csv`
