# Open Markdown Files From Windows Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pass valid Markdown launch arguments from the desktop process into frontend tabs.

**Architecture:** Add a pure startup argument filter in the Python desktop app. Pass its result into the bridge and dispatch a frontend event after mount; the existing validated `open_dropped_path` method supplies document payloads.

**Tech Stack:** Python, pywebview, Vue, pytest.

---

### Task 1: Startup argument filtering

**Files:**
- Modify: `desktop/src/flatnotes_desktop/app.py`
- Test: `desktop/tests/test_app.py`

- [ ] **Step 1: Write the failing test** for accepting existing `.md` files, rejecting non-Markdown/missing paths, and preserving order.
- [ ] **Step 2: Run the focused test and verify it fails** because the helper does not exist.
- [ ] **Step 3: Implement the minimal pure helper** and pass filtered paths into startup state.
- [ ] **Step 4: Run the focused test and verify it passes.**

### Task 2: Frontend launch event

**Files:**
- Modify: `desktop/src/flatnotes_desktop/app.py`
- Modify: `desktop/client/src/App.vue`
- Modify: `desktop/client/src/api/desktop.js`
- Test: `desktop/tests/test_app.py`

- [ ] **Step 1: Add a failing bridge/startup test** asserting valid launch paths are dispatched after frontend load.
- [ ] **Step 2: Implement launch-path retrieval/dispatch and frontend handling** using `openDroppedPath` and `tabs.open`.
- [ ] **Step 3: Run focused desktop tests and the frontend test suite.**

### Task 3: Final verification

**Files:** none.

- [ ] **Step 1: Run `pytest desktop/tests/test_app.py -q`.**
- [ ] **Step 2: Run `npm --prefix desktop/client test -- --run`.**
- [ ] **Step 3: Inspect `git diff` and report exact verification output.**
