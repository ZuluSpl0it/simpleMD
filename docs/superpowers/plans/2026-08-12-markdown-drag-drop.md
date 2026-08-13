# Markdown Drag-and-Drop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open multiple Markdown files dropped from Windows Explorer as separate Flatnotes tabs without allowing WebView2 to navigate away from the app.

**Architecture:** Register pywebview DOM `dragover` and `drop` handlers only from the post-load callback. Python extracts native `pywebviewFullPath` values, filters `.md` files, and dispatches one JSON-encoded `flatnotes-drop` browser event. Vue receives the ordered paths and opens each through the existing validated `open_dropped_path` bridge.

**Tech Stack:** Python 3, pywebview 6 DOM events, WebView2, Vue 3, Vitest, pytest, Vite.

---

### Task 1: Add the Python drop-event binding helper

**Files:**
- Modify: `desktop/src/flatnotes_desktop/app.py`
- Test: `desktop/tests/test_app.py`

- [ ] **Step 1: Write failing tests**

Add tests using fake `window.dom.document.events` and `window.evaluate_js` objects. Assert that `bind_drop_handlers(window)` attaches `dragover` and `drop` once, sets `prevent_default=True` on both, sets `stop_propagation=True` on drop, and is idempotent. Add a drop test whose files are `[one.md, ignore.txt, two.MD]`; assert one evaluate-js call contains the ordered JSON path list `[one.md, two.MD]`. Add an empty/invalid-entry test and assert no evaluate-js call occurs. Use a helper that extracts the JSON argument from the generated CustomEvent script rather than comparing the whole JavaScript string.

- [ ] **Step 2: Verify the tests fail**

Run:

```bash
UV_CACHE_DIR=/tmp/flatnotes-uv-cache uv run --project . pytest -q tests/test_app.py -k 'drop_handler or bind_drop'
```

Expected: FAIL because the drop binding helpers do not exist.

- [ ] **Step 3: Implement the minimal binding**

In `desktop/src/flatnotes_desktop/app.py`, import `json` and `DOMEventHandler` from `webview.dom`. Add `make_drop_handler(window)` that reads `event.get("dataTransfer", {}).get("files", [])`, extracts `pywebviewFullPath`, keeps only existing regular files whose suffix lowercases to `.md`, removes duplicate paths while preserving order, and returns without dispatching if none remain. For valid paths, call `window.evaluate_js` with a JSON-generated script that dispatches:

```python
window.dispatchEvent(new CustomEvent('flatnotes-drop', {detail: {paths: [...]}}))
```

Use `json.dumps(paths)` for the array; never concatenate raw paths into executable JavaScript. Catch malformed event data and return without dispatching.

Add idempotent `bind_drop_handlers(window)`. Assign `DOMEventHandler(lambda _event: None, prevent_default=True, stop_propagation=True, debounce=250)` to `window.dom.document.events.dragover`. Assign `DOMEventHandler(make_drop_handler(window), prevent_default=True, stop_propagation=True)` to `.drop`, then mark the window bound. Call this helper from `on_loaded` after the document is loaded; do not register DOM handlers from `startup_callback`.

- [ ] **Step 4: Verify focused tests pass**

Run the focused pytest command again; all drop-binding tests must pass.

- [ ] **Step 5: Commit**

```bash
git add desktop/src/flatnotes_desktop/app.py desktop/tests/test_app.py
git commit -m "feat: bind native markdown drop events"
```

### Task 2: Open multiple dropped paths in Vue tabs

**Files:**
- Modify: `desktop/client/src/App.vue`
- Create: `desktop/client/src/drop.test.js`

- [ ] **Step 1: Write the failing frontend test**

Create a source-level Vitest test for `App.vue` that asserts `handleDrop` reads `event.detail?.paths`, loops with `for (const path of paths)`, awaits `openDroppedPath(path)`, and opens successful documents with `tabs.open(classifyDocument(document, workspace.value))`. Add a second assertion that the existing single-document payload with `kind` and `path` remains supported.

- [ ] **Step 2: Verify it fails**

Run `npm test -- --run src/drop.test.js`. Expected: FAIL because the current handler expects one document instead of a path list.

- [ ] **Step 3: Implement ordered multi-file opening**

Update `handleDrop` so it reads `event.detail || {}`, loops over an array `payload.paths`, awaits `openDroppedPath(path)` in order, opens only successful external documents via `classifyDocument`, and catches an individual error so later paths still open. If no path array exists, retain compatibility with the existing single-document payload by opening a payload containing `kind` and `path`. Keep the existing event listener cleanup.

The intended core is:

```js
async function handleDrop(event) {
  const payload = event.detail || {};
  const paths = Array.isArray(payload.paths) ? payload.paths : [];
  for (const path of paths) {
    try {
      const document = await openDroppedPath(path);
      if (document?.kind === "external") tabs.open(classifyDocument(document, workspace.value));
    } catch (_error) {
      // Continue opening the remaining files in this drop.
    }
  }
  if (!paths.length && payload.kind && payload.path) {
    tabs.open(classifyDocument(payload, workspace.value));
  }
}
```

- [ ] **Step 4: Verify focused test passes**

Run `npm test -- --run src/drop.test.js`; both assertions must pass.

- [ ] **Step 5: Commit**

```bash
git add desktop/client/src/App.vue desktop/client/src/drop.test.js
git commit -m "feat: open multiple dropped markdown files"
```

### Task 3: Complete verification and refresh Windows assets

**Files:**
- Modify: generated `desktop/client/dist/index.html` and `desktop/client/dist/assets/*`
- Copy: `/mnt/c/src/client/` and `/mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/`

- [ ] **Step 1: Run all tests**

Run the frontend command from `desktop/client`:

```bash
npm test -- --run
```

Then run the Python command from `desktop`:

```bash
UV_CACHE_DIR=/tmp/flatnotes-uv-cache uv run --project . pytest -q
```

Expected: every frontend and Python test passes.

- [ ] **Step 2: Build**

From `desktop/client`, run `npm run build`; expect a successful Vite build with current hashed JS/CSS files.

- [ ] **Step 3: Refresh `C:\src`**

Copy the changed Python/frontend source and the complete `desktop/client/dist` output to `/mnt/c/src/client`. Copy `index.html` and the current hashed assets to `/mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets` and its `assets/` child. Remove only superseded hashed bundles no longer referenced by the new index. Verify copied files with `sha256sum` and verify both Windows index files reference only current hashes.

- [ ] **Step 4: Check and commit**

Run:

```bash
git diff --check
git status --short
```

Then commit the verified implementation:

```bash
git add desktop docs/superpowers/plans/2026-08-12-markdown-drag-drop.md
git commit -m "feat: support multi-file markdown drag and drop"
```

Manual Windows check: restart the packaged app, drag one `.md`, then several `.md` files. Confirm one tab opens per file, the last is active, mixed non-Markdown drops do not navigate away, and existing tabs remain open.
