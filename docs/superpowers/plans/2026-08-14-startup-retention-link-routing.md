# Startup Retention and Link Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Retain only five startup logs and route rendered Markdown links to anchors, the system browser/file handler, or new Flatnotes tabs.

**Architecture:** Startup retention runs immediately after the current trace opens and remains failure-safe. A pure frontend classifier decides link category; Python launches external targets and resolves Markdown paths; the frontend turns returned documents into tabs.

**Tech Stack:** Python 3.13, pywebview, pathlib, webbrowser, Vue 3, Toast UI Editor, Vitest, pytest, Vite.

---

### Task 1: Retain five startup logs

**Files:**
- Modify: desktop/src/flatnotes_desktop/startup.py
- Modify: desktop/src/flatnotes_desktop/app.py
- Test: desktop/tests/test_app.py

- [ ] **Step 1: Write failing retention tests**

Add tests that create seven timestamped logs plus a current trace, assert that
five remain, and monkeypatch Path.unlink to raise OSError while asserting the
pruner does not raise.

~~~python
def test_prune_startup_logs_keeps_current_and_four_newest_previous_logs(tmp_path):
    from flatnotes_desktop.startup import prune_startup_logs
    log_dir = tmp_path / "startup-logs"
    log_dir.mkdir()
    logs = []
    for index in range(7):
        path = log_dir / f"startup-20260812T14050{index}.000000Z-1.log"
        path.write_text(str(index), encoding="utf-8")
        logs.append(path)
    current = log_dir / "startup-20260813T140500.000000Z-99.log"
    current.write_text("current", encoding="utf-8")
    prune_startup_logs(log_dir, current, keep=5)
    assert len(list(log_dir.glob("*.log"))) == 5
    assert current.exists()
    assert logs[-1].exists()
    assert not logs[0].exists()
~~~

- [ ] **Step 2: Run the focused test and verify the expected failure**

From desktop/:

~~~bash
.venv/bin/python -m pytest tests/test_app.py -k prune_startup_logs -q
~~~

Expected: FAIL because prune_startup_logs is undefined.

- [ ] **Step 3: Implement and invoke the failure-safe pruner**

Add this to startup.py:

~~~python
def prune_startup_logs(log_directory: Path, current_path: Path, keep: int = 5) -> None:
    try:
        candidates = sorted(
            (path for path in log_directory.glob("*.log") if path.is_file()),
            key=lambda path: path.name,
            reverse=True,
        )
        retained = {current_path}
        for path in candidates:
            if len(retained) >= max(1, keep):
                break
            retained.add(path)
        for path in candidates:
            if path not in retained:
                try:
                    path.unlink()
                except OSError:
                    pass
    except OSError:
        pass
~~~

In app.py, replace direct trace construction with:

~~~python
trace_path = startup_trace_path(data_directory)
trace = StartupTrace(trace_path)
prune_startup_logs(trace_path.parent, trace_path)
~~~

- [ ] **Step 4: Run all Python tests and commit**

~~~bash
.venv/bin/python -m pytest -q
git add desktop/src/flatnotes_desktop/startup.py desktop/src/flatnotes_desktop/app.py desktop/tests/test_app.py
git commit -m "feat: retain five startup logs"
~~~

---

### Task 2: Add Python link-opening and Markdown-link resolution

**Files:**
- Modify: desktop/src/flatnotes_desktop/bridge.py
- Test: desktop/tests/test_bridge.py

- [ ] **Step 1: Write failing bridge tests**

Test that open_external_link delegates an HTTPS URL to webbrowser.open, that
open_markdown_link resolves parts/setup.md#install relative to the current file
and returns its document payload, and that missing or non-Markdown targets
return an error.

~~~python
def test_open_external_link_uses_browser_adapter(monkeypatch):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    import webbrowser
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    bridge = DesktopBridge(FakeWindow(None), FileService())
    assert bridge.open_external_link("https://example.com/docs") is True
    assert opened == ["https://example.com/docs"]


def test_open_markdown_link_resolves_relative_to_current_file(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    source = tmp_path / "guide.md"
    target = tmp_path / "parts" / "setup.md"
    target.parent.mkdir()
    source.write_text("body", encoding="utf-8")
    target.write_text("# Install", encoding="utf-8")
    bridge = DesktopBridge(FakeWindow(None), FileService())
    result = bridge.open_markdown_link(str(source), "parts/setup.md#install")
    assert result["path"] == str(target.resolve())
    assert result["content"] == "# Install"
~~~

- [ ] **Step 2: Run the focused tests and verify they fail**

~~~bash
.venv/bin/python -m pytest tests/test_bridge.py -k "external_link or markdown_link" -q
~~~

Expected: FAIL because the bridge methods do not exist.

- [ ] **Step 3: Implement the bridge**

Validate only HTTP(S) in open_external_link and call webbrowser.open. In
open_markdown_link, parse the URL, preserve HTTP(S) as browser routes, reject
unsupported schemes, resolve relative paths from current_path, discard the
fragment, and return a document payload for existing .md files. For other
local files, call os.startfile on Windows and webbrowser.open(path.as_uri())
elsewhere. Convert filesystem errors to {"error": ...} results.

- [ ] **Step 4: Run all Python tests and commit**

~~~bash
.venv/bin/python -m pytest -q
git add desktop/src/flatnotes_desktop/bridge.py desktop/tests/test_bridge.py
git commit -m "feat: route links through desktop bridge"
~~~

---

### Task 3: Route rendered links in the frontend

**Files:**
- Create: desktop/client/src/linkRouting.js
- Create: desktop/client/src/linkRouting.test.js
- Modify: desktop/client/src/api/desktop.js
- Modify: desktop/client/src/components/MarkdownEditor.vue
- Modify: desktop/client/src/App.vue

- [ ] **Step 1: Write failing classifier tests**

Create linkRouting.test.js with one test for each route:

~~~js
import { describe, expect, it, vi } from "vitest";
import { classifyLink, routeLinkClick } from "./linkRouting.js";

describe("classifyLink", () => {
  it("leaves anchors in the current document", () => {
    expect(classifyLink("#install")).toEqual({ kind: "anchor" });
  });
  it("routes web URLs to the browser", () => {
    expect(classifyLink("https://example.com/a")).toEqual({ kind: "browser", href: "https://example.com/a" });
  });
  it("routes Markdown paths to a new tab", () => {
    expect(classifyLink("parts/setup.md#install")).toEqual({ kind: "markdown", href: "parts/setup.md#install" });
  });
  it("routes other local paths to the system handler", () => {
    expect(classifyLink("assets/diagram.png")).toEqual({ kind: "file", href: "assets/diagram.png" });
  });
  it("prevents navigation only for non-anchor routes", () => {
    const preventDefault = vi.fn();
    const anchor = { getAttribute: () => "parts/setup.md" };
    const event = { target: { closest: () => anchor }, preventDefault };
    const routed = [];
    expect(routeLinkClick(event, "C:/Notes/guide.md", routed.push)).toBe(true);
    expect(preventDefault).toHaveBeenCalledOnce();
    expect(routed[0]).toEqual({ kind: "markdown", href: "parts/setup.md", path: "C:/Notes/guide.md" });
  });
});
~~~

- [ ] **Step 2: Run the focused test and verify the expected failure**

~~~bash
npm test -- src/linkRouting.test.js
~~~

Expected: FAIL because linkRouting.js does not exist.

- [ ] **Step 3: Implement classification and API wrappers**

Create linkRouting.js:

~~~js
export function classifyLink(href) {
  const value = String(href || "");
  if (!value || value.startsWith("#")) return { kind: "anchor" };
  const parsed = new URL(value, "file:///flatnotes/current.md");
  if (parsed.protocol === "http:" || parsed.protocol === "https:") return { kind: "browser", href: value };
  if (parsed.protocol === "file:" && parsed.pathname.toLowerCase().endsWith(".md")) return { kind: "markdown", href: value };
  if (parsed.protocol === "file:") return { kind: "file", href: value };
  return { kind: "file", href: value };
}

export function routeLinkClick(event, currentPath, onRoute) {
  const anchor = event.target?.closest?.("a[href]");
  if (!anchor) return false;
  const route = classifyLink(anchor.getAttribute("href"));
  if (route.kind === "anchor") return false;
  event.preventDefault();
  onRoute({ ...route, path: currentPath });
  return true;
}
~~~

Add to api/desktop.js:

~~~js
export const openExternalLink = (url) => call("open_external_link", url);
export const openMarkdownLink = (currentPath, href) => call("open_markdown_link", currentPath, href);
~~~

- [ ] **Step 4: Emit rendered link clicks from MarkdownEditor**

Add a path prop and link-click emit to MarkdownEditor.vue. Register one click
listener on the editor container and call routeLinkClick with props.path and an
emit callback. Anchor links return false and retain normal scrolling; other
routes are prevented and emitted as { kind, href, path: props.path }. Remove
the listener in onBeforeUnmount.

- [ ] **Step 5: Open browser links and Markdown links from App.vue**

Pass the active tab path to MarkdownEditor and handle link-click:

~~~js
async function handleEditorLink({ kind, href, path }) {
  try {
    if (kind === "browser") {
      await openExternalLink(href);
      return;
    }
    const result = await openMarkdownLink(path, href);
    if (result?.error) throw new Error(result.error);
    if (result?.content !== undefined) tabs.open(classifyDocument(result, workspace.value));
  } catch (error) {
    window.alert("Could not open link: " + error.message);
  }
}
~~~

Add the handler to MarkdownEditor with the link-click event. The bridge
handles local non-Markdown files and returns Markdown payloads for new tabs.

- [ ] **Step 6: Run frontend tests, build, and commit**

~~~bash
npm test
npm run build
git add desktop/client/src/linkRouting.js desktop/client/src/linkRouting.test.js desktop/client/src/api/desktop.js desktop/client/src/components/MarkdownEditor.vue desktop/client/src/App.vue
git commit -m "feat: open rendered links externally or in tabs"
~~~

Expected: all frontend tests pass and Vite emits a production bundle.

---

### Task 4: Synchronize Windows source and built frontend

**Files:**
- Copy: desktop/src/ to /mnt/c/src/src/
- Copy: desktop/tests/ to /mnt/c/src/tests/
- Copy: desktop/client/src/ to /mnt/c/src/client/src/
- Copy: desktop/client/dist/ to /mnt/c/src/client/dist/
- Copy: desktop/client/dist/ to /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/

- [ ] **Step 1: Copy source and assets**

~~~bash
cp -r desktop/src/. /mnt/c/src/src/
cp -r desktop/tests/. /mnt/c/src/tests/
cp -r desktop/client/src/. /mnt/c/src/client/src/
cp -r desktop/client/dist/. /mnt/c/src/client/dist/
cp -r desktop/client/dist/. /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/
~~~

- [ ] **Step 2: Verify source and entry-file synchronization**

~~~bash
diff -qr desktop/src /mnt/c/src/src
diff -qr desktop/client/src /mnt/c/src/client/src
diff -q desktop/client/dist/index.html /mnt/c/src/client/dist/index.html
diff -q desktop/client/dist/index.html /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/index.html
~~~

Expected: no output and successful exit status for every comparison. A
Windows PyInstaller rebuild is required before distributing the updated exe.
