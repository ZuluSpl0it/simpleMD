# Find and Replace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add edit-mode Replace and Replace All actions to the existing Ctrl+F find bar while keeping viewing mode find-only.

**Architecture:** Keep tab Markdown source as the replacement source of truth. Add pure literal, case-insensitive replacement helpers beside `findMatches`, expose replacement controls from `FindBar` only when editing, and have `App.vue` apply changed content through `tabs.setContent` so dirty-state and Toast UI synchronization remain unchanged.

**Tech Stack:** Vue 3, Toast UI Editor, Vitest, Vite, Python/pytest regression suite, WebView2 packaged assets.

---

### Task 1: Add tested source replacement helpers

**Files:**
- Modify: `desktop/client/src/find.js`
- Test: `desktop/client/src/find.test.js`

- [ ] **Step 1: Write failing unit tests**

Add tests for these exact behaviors:

```js
import { findMatches, replaceAllMatches, replaceMatch } from "./find.js";

it("replaces only the active case-insensitive match", () => {
  expect(replaceMatch("One one ONE", "one", "two", 1)).toBe("One two ONE");
});

it("replaces every non-overlapping match", () => {
  expect(replaceAllMatches("Flatnotes notes FLATNOTES", "notes", "docs")).toBe("Flatdocs docs FLATdocs");
});

it("treats replacement text literally and makes invalid requests no-ops", () => {
  expect(replaceAllMatches("a.b A.B", "a.b", "$& [x]")).toBe("$& [x] $& [x]");
  expect(replaceMatch("content", "", "x", 0)).toBe("content");
  expect(replaceMatch("one", "missing", "x", 0)).toBe("one");
  expect(replaceMatch("one", "one", "x", 4)).toBe("one");
});
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run from `desktop/client`:

```bash
npm test -- --run src/find.test.js
```

Expected: FAIL because `replaceMatch` and `replaceAllMatches` are not exported yet.

- [ ] **Step 3: Implement literal replacement helpers**

In `desktop/client/src/find.js`, add:

```js
export function replaceMatch(text, query, replacement, activeIndex = 0) {
  const matches = findMatches(text, query);
  const match = matches[activeIndex];
  if (!match) return text;
  return text.slice(0, match.start) + replacement + text.slice(match.end);
}

export function replaceAllMatches(text, query, replacement) {
  const matches = findMatches(text, query);
  if (!matches.length) return text;
  let result = text;
  for (let index = matches.length - 1; index >= 0; index -= 1) {
    const match = matches[index];
    result = result.slice(0, match.start) + replacement + result.slice(match.end);
  }
  return result;
}
```

The existing `findMatches` already trims the query, lowercases for matching, and returns non-overlapping source offsets. Reverse-order replacement prevents earlier offsets from shifting. Do not use a regex so replacement text remains literal.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run `npm test -- --run src/find.test.js`; all find/replacement tests must pass.

- [ ] **Step 5: Commit the helper**

```bash
git add desktop/client/src/find.js desktop/client/src/find.test.js
git commit -m "feat: add literal find replacement helpers"
```

### Task 2: Add edit-only replacement controls to FindBar

**Files:**
- Modify: `desktop/client/src/components/FindBar.vue`
- Create: `desktop/client/src/components/FindBar.test.js`
- Modify: `desktop/client/src/style.css`

- [ ] **Step 1: Write the failing component/source test**

Create a source-level Vitest test that reads `FindBar.vue` and asserts:

```js
expect(source).toMatch(/editing/);
expect(source).toMatch(/v-if="editing"/);
expect(source).toMatch(/Replace/);
expect(source).toMatch(/Replace All/);
expect(source).toMatch(/update:replacement/);
expect(source).toMatch(/replace-all/);
```

Also assert that the replacement input and both buttons are inside the `v-if="editing"` block, so viewing mode remains find-only.

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
npm test -- --run src/components/FindBar.test.js
```

Expected: FAIL because FindBar currently has no editing prop or replacement controls.

- [ ] **Step 3: Implement the minimal FindBar UI**

Update `FindBar.vue` to:

1. Accept `editing` and `replacement` props.
2. Emit `update:replacement`, `replace`, and `replace-all` in addition to existing events.
3. Keep the existing find input, count, navigation buttons, and close button unchanged.
4. Render only when `editing` is true:

```vue
<template v-if="editing">
  <input
    :value="replacement"
    type="text"
    placeholder="Replace with"
    aria-label="Replace with"
    @input="$emit('update:replacement', $event.target.value)"
    @keydown.enter.prevent="$emit('replace')"
  />
  <button type="button" :disabled="!matchCount" @click="$emit('replace')">Replace</button>
  <button type="button" :disabled="!matchCount" @click="$emit('replace-all')">Replace All</button>
</template>
```

Use the existing bar layout; add a narrow replacement input and allow the action buttons to wrap or fit without changing the editor area. Add light-theme input styling by extending the existing `.find-bar input` selectors if needed.

- [ ] **Step 4: Run the focused component test and verify it passes**

Run `npm test -- --run src/components/FindBar.test.js`; the edit-only control assertions must pass.

- [ ] **Step 5: Commit the FindBar controls**

```bash
git add desktop/client/src/components/FindBar.vue desktop/client/src/components/FindBar.test.js desktop/client/src/style.css
git commit -m "feat: add edit-mode replace controls"
```

### Task 3: Wire replacement through App and tab dirty state

**Files:**
- Modify: `desktop/client/src/App.vue`
- Create: `desktop/client/src/replace.test.js`

- [ ] **Step 1: Write the failing App wiring test**

Create a source-level Vitest test that asserts `App.vue` imports both replacement helpers, passes `editing` and `replacement` to FindBar, listens for `replace` and `replace-all`, and applies updates with `tabs.setContent`:

```js
expect(source).toMatch(/replaceMatch/);
expect(source).toMatch(/replaceAllMatches/);
expect(source).toMatch(/:editing="tabs\.active\.value\.editing"/);
expect(source).toMatch(/:replacement="replacementQuery"/);
expect(source).toMatch(/@replace="replaceActive"/);
expect(source).toMatch(/@replace-all="replaceAllActive"/);
expect(source).toMatch(/tabs\.setContent/);
```

- [ ] **Step 2: Run it and verify it fails**

Run `npm test -- --run src/replace.test.js`. Expected: FAIL because App does not yet own a replacement query or replacement handlers.

- [ ] **Step 3: Implement App replacement wiring**

In `App.vue`:

1. Import `replaceMatch` and `replaceAllMatches` from `find.js`.
2. Add `const replacementQuery = ref("");`.
3. Pass to FindBar:

```vue
<FindBar
  v-if="findOpen && tabs.active.value"
  :query="findQuery"
  :replacement="replacementQuery"
  :editing="tabs.active.value.editing"
  :match-count="findCount"
  :active-match="findIndex"
  @update:query="setFindQuery"
  @update:replacement="replacementQuery = $event"
  @previous="moveFind(-1)"
  @next="moveFind(1)"
  @replace="replaceActive"
  @replace-all="replaceAllActive"
  @close="closeFind"
/>
```

4. Reset `replacementQuery` in `closeFind`.
5. Add `replaceActive()` and `replaceAllActive()` that return unless the active tab is editing and the find query is non-empty. Compute new content with the corresponding helper, and call `tabs.setContent(tab.id, nextContent)` only when content changes. Keep the find query and replacement query after the operation so highlights and counts refresh.
6. If Replace removes the active match, clamp `findIndex` to the new `findCount` in the existing `setFindCount` path; do not close the find bar.

Because `tabs.setContent` is already the dirty-state path and `MarkdownEditor` watches `props.content`, no direct Toast UI mutation is needed.

- [ ] **Step 4: Run focused App tests and the complete frontend suite**

Run:

```bash
npm test -- --run src/replace.test.js
npm test -- --run
```

Expected: the replacement wiring test and all frontend tests pass.

- [ ] **Step 5: Commit App wiring**

```bash
git add desktop/client/src/App.vue desktop/client/src/replace.test.js
git commit -m "feat: wire find and replace into active tabs"
```

### Task 4: Build, verify, and refresh Windows assets

**Files:**
- Modify: generated `desktop/client/dist/index.html` and `desktop/client/dist/assets/*`
- Copy: `/mnt/c/src/client/` and `/mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/`

- [ ] **Step 1: Run complete frontend and Python suites**

From `desktop/client`, run `npm test -- --run`. From `desktop`, run `UV_CACHE_DIR=/tmp/flatnotes-uv-cache uv run --project . pytest -q`. Expected: all tests pass.

- [ ] **Step 2: Build the frontend**

From `desktop/client`, run `npm run build`. Expected: Vite exits successfully and writes current hashed JavaScript/CSS assets.

- [ ] **Step 3: Copy verified source and frontend assets to `C:\src`**

Copy changed frontend source/tests into `/mnt/c/src/client/src`, copy `desktop/client/dist` to `/mnt/c/src/client/dist`, and copy the generated `index.html` plus current hashed bundles to `/mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets` and its `assets` child. Remove only old hashed bundles no longer referenced by the new index. Verify matching SHA-256 hashes and index references.

- [ ] **Step 4: Run repository checks and commit**

Run `git diff --check` and inspect `git status --short`. Commit with:

```bash
git add desktop docs/superpowers/plans/2026-08-13-find-replace.md
git commit -m "feat: add find and replace"
```

Manual check: restart the refreshed app, open a document in viewing mode and confirm Ctrl+F has no replacement controls. Enter Edit mode, press Ctrl+F, replace one match, then replace all matches, and confirm Save persists the changes.
