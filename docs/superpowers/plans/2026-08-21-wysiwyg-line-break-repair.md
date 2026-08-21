# WYSIWYG Line Break Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve literal Markdown `<br>` tags across Markdown/WYSIWYG mode switches and insert reliable real line breaks from the toolbar without crashing or blanking the editor.

**Architecture:** Keep `<br>` as the application-facing Markdown representation. Before WYSIWYG conversion, use Toast UI's Markdown AST source positions to replace only semantic HTML break nodes with a private marker; Toast UI's supported widget parser converts that marker into a real DOM `<br>`. Normalize markers and widget wrappers back to `<br>` whenever content leaves the editor.

**Tech Stack:** Vue 3, Toast UI Editor 3.2.2, Vitest, Playwright browser diagnostic, Vite.

---

### Task 1: Define and test line-break boundary transforms

**Files:**
- Modify: `desktop/client/src/soft-break.test.js`
- Modify: `desktop/client/src/softBreaks.js`

- [ ] **Step 1: Add failing tests for AST-aware encoding and editor-output decoding**

Add tests proving that an `htmlInline` `<br>` node is replaced with a private marker, code nodes containing `<br>` are unchanged, consecutive widget wrappers decode to consecutive `<br>` tags, and WYSIWYG insertion creates a widget containing the private marker.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `npm test -- --run src/soft-break.test.js`

Expected: FAIL because the AST encoding and normalized decoding functions do not exist and the current widget stores raw `<br>`.

- [ ] **Step 3: Implement the minimal transform helpers**

Implement:

```js
export const lineBreakMarker = "\uE000simplemd-br\uE001";

export function encodeHtmlLineBreaks(markdown, rootNode) {
  const lineOffsets = [0];
  for (let index = 0; index < markdown.length; index += 1) {
    if (markdown[index] === "\n") lineOffsets.push(index + 1);
  }
  const replacements = [];
  const walker = rootNode?.walker();
  let event;
  while (walker && (event = walker.next())) {
    const node = event.node;
    if (!event.entering || !isBreakTag(node) || !node.sourcepos) continue;
    const [[startLine, startColumn], [endLine, endColumn]] = node.sourcepos;
    replacements.push({
      start: lineOffsets[startLine - 1] + startColumn - 1,
      end: lineOffsets[endLine - 1] + endColumn,
    });
  }
  return replacements
    .sort((left, right) => right.start - left.start)
    .reduce(
      (result, { start, end }) => `${result.slice(0, start)}${lineBreakMarker}${result.slice(end)}`,
      markdown,
    );
}

export function decodeEditorLineBreaks(markdown) {
  return markdown
    .replace(new RegExp(`\\$\\$widget\\d+\\s+${lineBreakMarker}\\$\\$`, "g"), "<br>")
    .replaceAll(lineBreakMarker, "<br>");
}

export function markdownForWysiwyg(editor, markdown) {
  const ToastMark = editor?.toastMark?.constructor;
  if (!ToastMark) return markdown;
  const parsed = new ToastMark(markdown);
  return encodeHtmlLineBreaks(markdown, parsed.getRootNode());
}
```

Update `insertWysiwygLineBreak()` so its valid Toast UI widget contains `$$widget0 ${lineBreakMarker}$$`. Remove the direct `htmlInline` converter from `configureWysiwygSoftBreaks()`; retain only existing soft-break rendering behavior.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `npm test -- --run src/soft-break.test.js`

Expected: all line-break helper tests pass.

### Task 2: Integrate valid widgets at the editor boundary

**Files:**
- Modify: `desktop/client/src/components/MarkdownEditor.vue`
- Modify: `desktop/client/src/editor-mode.test.js`

- [ ] **Step 1: Add failing integration-structure tests**

Assert that the component's widget rule matches only `lineBreakMarker`, Markdown-to-WYSIWYG switching calls `markdownForWysiwyg()` before Toast UI handles the click, emitted content calls `decodeEditorLineBreaks()`, Markdown mode restores literal `<br>`, and the prop watcher ignores the normalized echo from the parent.

- [ ] **Step 2: Run the focused tests and verify RED**

Run: `npm test -- --run src/editor-mode.test.js src/soft-break.test.js`

Expected: FAIL because the component still registers a raw `<br>` widget rule and directly emits Toast UI's internal Markdown.

- [ ] **Step 3: Implement the editor boundary**

In `MarkdownEditor.vue`:

```js
widgetRules: [{
  rule: new RegExp(lineBreakMarker),
  toDOM: () => document.createElement("br"),
}]
```

Add a capture-phase mode-switch handler that encodes semantic `<br>` nodes immediately before Markdown switches to WYSIWYG. Decode content in change handlers, restore decoded Markdown after switching back, track the last emitted normalized content so the Vue prop watcher does not overwrite valid internal widgets, and encode true external updates while WYSIWYG is active.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `npm test -- --run src/editor-mode.test.js src/soft-break.test.js`

Expected: both files pass.

### Task 3: Verify the real editor and mirror Windows sources

**Files:**
- Modify: `/tmp/reproduce_simplemd_wysiwyg.py` (diagnostic only, not committed)
- Mirror: `C:\src\client\src\components\MarkdownEditor.vue`
- Mirror: `C:\src\client\src\softBreaks.js`
- Mirror: corresponding focused test files

- [ ] **Step 1: Turn the existing browser reproduction into an assertion-based regression check**

Assert no page errors, WYSIWYG becomes active, its ProseMirror HTML contains real `<br>` elements and surrounding text, and switching back exposes literal `<br>` Markdown.

- [ ] **Step 2: Run the browser check**

Run the local Vite server and `python3 -u /tmp/reproduce_simplemd_wysiwyg.py`.

Expected: PASS; the prior `getWidgetContent()` null-child stack trace is absent.

- [ ] **Step 3: Run bounded project verification**

Run:

```bash
npm test -- --run
npm run build
git diff --check
```

Expected: all frontend tests pass, Vite production build succeeds, and no whitespace errors are reported.

- [ ] **Step 4: Mirror and byte-compare Windows files**

Copy the four modified frontend source/test files into `C:\src\client\src` and run `diff -q` against each source copy.

Expected: all comparisons are identical.
