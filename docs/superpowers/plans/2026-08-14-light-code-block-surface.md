# Light Code-Block Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give reader and WYSIWYG code blocks a visibly darker background in the light theme without changing Markdown source editing or dark mode.

**Architecture:** Keep the change in the desktop client theme stylesheet. A light-theme selector targets Toast UI rendered `pre` elements, which are shared by reader and WYSIWYG output. A source-contract Vitest test locks in the selector and exact neutral color.

**Tech Stack:** Vue 3, Toast UI Editor, CSS, Vitest, Vite.

---

### Task 1: Specify the light code-block surface

**Files:**
- Modify: `desktop/client/src/style.test.js`
- Modify: `desktop/client/src/style.css`

- [ ] **Step 1: Add a failing stylesheet contract test**

Append this test to `desktop/client/src/style.test.js`:

```js
it("uses a darker code-block surface in rendered light-theme views", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(
    /:root\[data-theme="light"\]\s+\.toastui-editor-contents\s+pre\s*\{[^}]*background:\s*#e7e5e4/,
  );
});
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run:

```bash
npm test -- --run desktop/client/src/style.test.js
```

Expected: FAIL because the light-theme `pre` background rule does not yet exist.

- [ ] **Step 3: Add the minimum light-theme CSS rule**

In `desktop/client/src/style.css`, after the light-theme modal rules, add:

```css
:root[data-theme="light"] .toastui-editor-contents pre { background: #e7e5e4; }
```

This selector matches Toast UI rendered code blocks in both reader and WYSIWYG. Do not add a rule for `.toastui-editor-md-container`, and do not change any dark-theme selector.

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```bash
npm test -- --run desktop/client/src/style.test.js
```

Expected: PASS, including the new code-block surface test.

- [ ] **Step 5: Run the full frontend verification**

Run:

```bash
npm test
npm run build
```

Expected: all Vitest tests pass and Vite emits `dist/index.html` plus hashed assets without an error.

- [ ] **Step 6: Commit the source and test**

Run:

```bash
git add desktop/client/src/style.css desktop/client/src/style.test.js
git commit -m "style: darken light theme code blocks"
```

### Task 2: Synchronize the Windows source and runnable portable app

**Files:**
- Copy: `desktop/client/src/style.css` to `/mnt/c/src/client/src/style.css`
- Copy: `desktop/client/src/style.test.js` to `/mnt/c/src/client/src/style.test.js`
- Copy: `desktop/client/dist/` to `/mnt/c/src/client/dist/`
- Copy: `desktop/client/dist/` to `/mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/`

- [ ] **Step 1: Confirm the build output names that must be synchronized**

Run:

```bash
find desktop/client/dist -maxdepth 2 -type f | sort
```

Expected: `index.html` and the current hashed JavaScript and CSS bundles.

- [ ] **Step 2: Copy the rebuilt client source and distribution to Windows**

Run:

```bash
cp desktop/client/src/style.css /mnt/c/src/client/src/style.css
cp desktop/client/src/style.test.js /mnt/c/src/client/src/style.test.js
cp -r desktop/client/dist/. /mnt/c/src/client/dist/
cp -r desktop/client/dist/. /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/
```

Expected: the Windows source mirror and portable app assets contain the rebuilt client output.

- [ ] **Step 3: Verify the important source and entry-file synchronization**

Run:

```bash
diff -q desktop/client/src/style.css /mnt/c/src/client/src/style.css
diff -q desktop/client/src/style.test.js /mnt/c/src/client/src/style.test.js
diff -q desktop/client/dist/index.html /mnt/c/src/client/dist/index.html
diff -q desktop/client/dist/index.html /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/index.html
```

Expected: all four commands produce no output and exit successfully.

- [ ] **Step 4: Manually verify the runnable portable app**

Open a Markdown file containing a fenced code block in `C:\\src\\dist\\Flatnotes`, switch to the light theme, and check reader then WYSIWYG. The code-block surface should be `#e7e5e4`, while the page remains `#fafaf9`; Markdown source editing and dark mode should remain visually unchanged.
