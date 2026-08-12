# Markdown Drag-and-Drop Design

## Goal

Allow users to drag multiple Markdown files from Windows Explorer onto Flatnotes. Each valid `.md` file opens in its own tab, in the order supplied by the native drop event.

## Chosen approach

Use pywebview's native DOM drag-and-drop events. pywebview enriches dropped file records with `pywebviewFullPath`, which gives the Python side the native path needed to open files reliably. Register the handlers after the document has loaded so drag/drop setup does not participate in WebView2 startup or block the startup callback.

Browser-only JavaScript file drops are not sufficient because the browser `File` object does not provide a dependable native path for this desktop workflow. Direct Windows HWND/OLE integration would add platform-specific complexity without improving the required behavior.

## Data flow

1. `window.events.loaded` invokes a small binding function once the frontend document is ready.
2. A Python `DOMEventHandler` on `dragover` prevents the browser's default navigation behavior. It uses propagation controls and a debounce suitable for a high-frequency event.
3. A Python `DOMEventHandler` on `drop` reads `event["dataTransfer"]["files"]` and extracts each file's `pywebviewFullPath`.
4. The handler filters paths case-insensitively to the `.md` extension and ignores folders, missing paths, and unsupported files.
5. Python dispatches one browser `flatnotes-drop` event containing the ordered list of accepted paths. The payload is JSON-encoded rather than interpolated into executable JavaScript.
6. Vue handles the event by opening each path through the existing `open_dropped_path` bridge and opening each returned document in a new tab.
7. A failed individual file does not prevent later files in the same drop from opening. Invalid or empty drops produce no tabs and no navigation.

## Lifecycle and safety

- Bind drop handlers exactly once, after `loaded`; do not register them from the startup callback. The binding function must be idempotent so a repeated `loaded` notification cannot duplicate handlers. Window teardown needs no separate cleanup because the handlers belong to the closing window.
- Preserve the existing backend validation in `open_dropped_path`: only regular `.md` files are opened.
- Keep the existing `flatnotes-drop` listener cleanup in Vue.
- Do not use `eval` or concatenate untrusted paths into executable statements. Serialize the path list with JSON and dispatch a `CustomEvent`.
- Dropped files are external documents unless they are already classified as workspace documents by the existing frontend logic.

## User-visible behavior

- Dropping one Markdown file opens one tab.
- Dropping several Markdown files opens one tab per file in drop order, with the last opened document active.
- Dropping non-Markdown files, folders, or a mixed set silently skips unsupported entries.
- Existing tabs remain open; dropping files does not replace the current tab.
- The browser must not navigate away from Flatnotes when a file is dropped.

## Testing

### Python

- Verify the drop binding attaches `dragover` and `drop` handlers after the document loads.
- Verify the drop handler extracts multiple full paths, filters extensions, preserves order, and dispatches one JSON payload.
- Verify an empty or unsupported drop does not dispatch an open event.

### Frontend

- Verify a multi-path drop calls `openDroppedPath` for every path and opens every returned document in a separate tab.
- Verify one invalid/open failure does not prevent remaining paths from being attempted.
- Retain coverage for the existing single-document drop event for compatibility.

### Regression verification

- Run the complete Python suite.
- Run the complete frontend suite.
- Build the frontend and refresh the Windows source/package assets before manual testing.
