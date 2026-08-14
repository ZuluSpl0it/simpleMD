# Themed Save and Rename Input Dialogs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace browser-native save and rename prompts with themed, accessible in-app input dialogs.

**Architecture:** Add a focused `TextInputDialog.vue` component that owns only presentation and keyboard interaction. `App.vue` owns one pending request, opens the dialog for save or rename, and continues to call the existing bridge APIs only after a valid submission. Shared modal CSS keeps dark/light rendering consistent with the existing close dialog.

**Tech Stack:** Vue 3 `<script setup>`, Vitest, Vite, existing Flatnotes modal CSS and pywebview bridge APIs.

---

### Task 1: Add the reusable input dialog and behavior tests

**Files:**
- Create: `desktop/client/src/components/TextInputDialog.vue`
- Create: `desktop/client/src/components/TextInputDialog.test.js`

- [ ] **Step 1: Write the failing dialog behavior tests**

Create a source-level test that verifies the component contract and keyboard behavior:

```js
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const component = readFileSync(
  fileURLToPath(new URL("./TextInputDialog.vue", import.meta.url)),
  "utf8",
);

describe("TextInputDialog", () => {
  it("exposes a themed dialog with submit and cancel actions", () => {
    expect(component).toMatch(/role="dialog"/);
    expect(component).toMatch(/aria-modal="true"/);
    expect(component).toMatch(/@submit\.prevent="submit"/);
    expect(component).toMatch(/@click="submit"/);
    expect(component).toMatch(/@click="cancel"/);
    expect(component).toMatch(/@keydown\.escape="cancel"/);
  });

  it("accepts title, label, initial value, and action text", () => {
    expect(component).toMatch(/defineProps\(\{[^}]*title:/s);
    expect(component).toMatch(/defineProps\(\{[^}]*label:/s);
    expect(component).toMatch(/defineProps\(\{[^}]*value:/s);
    expect(component).toMatch(/defineProps\(\{[^}]*confirmLabel:/s);
    expect(component).toMatch(/defineEmits\(\["submit",\s*"cancel"\]/);
  });
});
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run from `desktop/client`:

```bash
npm test -- TextInputDialog.test.js
```

Expected: Vitest fails because `TextInputDialog.vue` does not exist.

- [ ] **Step 3: Implement the minimal dialog component**

Create a component with these exact responsibilities:

```vue
<template>
  <div class="modal-backdrop" role="presentation">
    <div class="text-input-dialog" role="dialog" aria-modal="true" aria-labelledby="text-input-dialog-title">
      <h2 id="text-input-dialog-title">{{ title }}</h2>
      <form @submit.prevent="submit">
        <label for="text-input-dialog-value">{{ label }}</label>
        <input id="text-input-dialog-value" ref="input" v-model="draft" type="text" autocomplete="off" @keydown.escape="cancel" />
        <div class="text-input-dialog-actions">
          <button type="submit">{{ confirmLabel }}</button>
          <button type="button" @click="cancel">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

const props = defineProps({
  title: { type: String, required: true },
  label: { type: String, required: true },
  value: { type: String, default: "" },
  confirmLabel: { type: String, default: "Save" },
});
const emit = defineEmits(["submit", "cancel"]);
const input = ref();
const draft = ref(props.value);
function submit() {
  const value = draft.value.trim();
  if (value) emit("submit", value);
}
function cancel() { emit("cancel"); }
onMounted(() => nextTick(() => input.value?.focus()));
</script>
```

- [ ] **Step 4: Add the shared dialog CSS**

Extend `desktop/client/src/style.css` beside `.close-dialog`:

```css
.text-input-dialog { min-width: 330px; max-width: min(460px, calc(100vw - 40px)); padding: 20px; border: 1px solid #78716c; border-radius: 8px; background: #292524; color: #f5f5f4; box-shadow: 0 8px 30px #0008; }
.text-input-dialog h2 { margin: 0 0 16px; font-size: 20px; }
.text-input-dialog label { display: block; margin-bottom: 6px; }
.text-input-dialog input { box-sizing: border-box; width: 100%; padding: 8px 10px; border: 1px solid #78716c; border-radius: 5px; background: #1c1917; color: #f5f5f4; }
.text-input-dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
:root[data-theme="light"] .text-input-dialog { border-color: #a8a29e; background: #ffffff; color: #292524; box-shadow: 0 8px 30px #57534e55; }
:root[data-theme="light"] .text-input-dialog input { border-color: #d6d3d1; background: #ffffff; color: #292524; }
```

- [ ] **Step 5: Test the component and CSS**

Run:

```bash
npm test -- TextInputDialog.test.js style.test.js
```

Expected: focused tests pass.

- [ ] **Step 6: Commit the self-contained dialog**

```bash
git add desktop/client/src/components/TextInputDialog.vue desktop/client/src/components/TextInputDialog.test.js desktop/client/src/style.css
git commit -m "feat: add themed text input dialog"
```

### Task 2: Replace save and rename prompts in App.vue

**Files:**
- Modify: `desktop/client/src/App.vue`
- Create: `desktop/client/src/inputDialog.test.js`

- [ ] **Step 1: Write failing App integration-contract tests**

Create a source-level test asserting that App mounts the dialog, routes submit/cancel, and contains no native prompt calls:

```js
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const app = readFileSync(fileURLToPath(new URL("./App.vue", import.meta.url)), "utf8");

it("uses the themed input dialog for save and rename", () => {
  expect(app).toMatch(/TextInputDialog/);
  expect(app).toMatch(/@submit="resolveInputDialog"/);
  expect(app).toMatch(/@cancel="cancelInputDialog"/);
  expect(app).toMatch(/inputDialog/);
  expect(app).not.toMatch(/window\.prompt\(/);
});
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```bash
npm test -- inputDialog.test.js
```

Expected: Vitest fails because App still uses `window.prompt()` and has no input-dialog state.

- [ ] **Step 3: Add App state and mount the dialog**

Import `TextInputDialog`, add `const inputDialog = ref(null)`, and render it after the existing dialogs:

```vue
<TextInputDialog
  v-if="inputDialog"
  :title="inputDialog.title"
  :label="inputDialog.label"
  :value="inputDialog.value"
  :confirm-label="inputDialog.confirmLabel"
  @submit="resolveInputDialog"
  @cancel="cancelInputDialog"
/>
```

The request object must contain `operation`, `title`, `label`, `value`, and `confirmLabel`.

- [ ] **Step 4: Replace saveActive and renameActive prompt calls**

Add:

```js
function requestInput(operation, title, label, value, confirmLabel) {
  inputDialog.value = { operation, title, label, value, confirmLabel };
}
function cancelInputDialog() { inputDialog.value = null; }
async function resolveInputDialog(value) {
  const request = inputDialog.value;
  inputDialog.value = null;
  if (!request) return;
  const tab = tabs.active.value;
  if (!tab) return;
  if (request.operation === "save") {
    const created = await createWorkspaceNote(value, tab.content);
    Object.assign(tab, { path: created.path, title: created.title, content: created.content, savedContent: created.content, dirty: false, modified_ns: created.modified_ns, content_hash: created.content_hash });
    return;
  }
  tab.renaming = true;
  try {
    const renamed = await renameWorkspaceNote(tab.title, value);
    Object.assign(tab, { title: renamed.title, path: renamed.path, modified_ns: renamed.modified_ns, content_hash: renamed.content_hash, externalState: null });
  } finally {
    tab.renaming = false;
  }
}
```

Change the no-path workspace branch of `saveActive()` to call:

```js
requestInput("save", "Save", "Note title", tab.title === "Untitled" ? "" : tab.title, "Save");
return;
```

Change `renameActive()` to call:

```js
requestInput("rename", "Rename", "New note title", tab.title, "Rename");
```

Keep the existing bridge calls and tab object assignments in the submit handler. Empty values are rejected by the dialog, and Cancel leaves state untouched.

- [ ] **Step 5: Run focused App tests**

Run:

```bash
npm test -- inputDialog.test.js TextInputDialog.test.js
```

Expected: all focused tests pass and no `window.prompt` remains in App.vue.

- [ ] **Step 6: Commit the App integration**

```bash
git add desktop/client/src/App.vue desktop/client/src/inputDialog.test.js
git commit -m "feat: use themed dialogs for save and rename"
```

### Task 3: Full verification and Windows asset synchronization

**Files:**
- Verify: `desktop/client/src/components/TextInputDialog.vue`
- Verify: `desktop/client/src/App.vue`
- Verify: `desktop/client/src/style.css`
- Verify: `desktop/client/dist/`

- [ ] **Step 1: Run the complete frontend test suite**

From `desktop/client` run:

```bash
npm test
```

Expected: every Vitest file passes, including the existing 56 tests plus the new dialog tests.

- [ ] **Step 2: Build the production frontend**

```bash
npm run build
```

Expected: Vite exits 0 and writes `dist/index.html` plus current hashed assets.

- [ ] **Step 3: Sync source and assets to C:\\src**

Copy the changed client source and complete `desktop/client/dist` output to `/mnt/c/src/client`, then copy `index.html` and current hashed assets to `/mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets`. Verify SHA-256 hashes of the copied index and referenced JavaScript bundle match the source build.

- [ ] **Step 4: Run a browser smoke test**

Verify in both themes:

1. Create a new workspace note and press Ctrl+S.
2. Confirm the in-app dialog title is `Save`, the action is `Save`, and no `127.0.0.1:<port> says` text appears.
3. Cancel and confirm no note is created.
4. Rename a workspace note and confirm the dialog uses `Rename`.
5. Confirm Enter submits and Escape cancels.

- [ ] **Step 5: Commit the verified implementation**

```bash
git add desktop/client/src desktop/client/dist
git commit -m "feat: replace native prompts with themed dialogs"
```
