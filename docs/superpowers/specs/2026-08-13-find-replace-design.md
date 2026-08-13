# Find and Replace Design

## Goal

Extend Flatnotes’ existing Ctrl+F document search with replacement controls that are available only while editing a document.

## User experience

- In viewing mode, Ctrl+F shows the existing find-only bar.
- In edit mode, Ctrl+F shows the find field, a replacement field, and `Replace` / `Replace All` actions.
- `Replace` changes the currently selected match.
- `Replace All` changes every case-insensitive, non-overlapping match.
- Empty find text disables replacement actions.
- Replacement keeps the find query active so the updated count and highlights refresh immediately.
- Replacements mark the active tab dirty through the existing tab content update path. Saving remains unchanged.

## Architecture

The active tab remains the source of truth for document content. A small pure helper in `find.js` performs case-insensitive source-text replacement and returns the new text plus the resulting match information needed by the UI. `App.vue` owns the replacement field and applies the helper to `tabs.active.value.content` through `tabs.setContent`.

`FindBar.vue` receives an `editing` prop. It renders replacement controls only when that prop is true and emits `update:replacement`, `replace`, and `replace-all` events. `App.vue` passes the active tab’s editing state and handles those events. The existing `MarkdownEditor` content watcher updates Toast UI after the tab content changes, regardless of Markdown or WYSIWYG mode.

## Replacement semantics

- Matching is case-insensitive, using the same trimmed query behavior as `findMatches`.
- Matching is non-overlapping and proceeds left-to-right.
- `Replace` uses the active match index from the current find result. If the index is no longer valid, it safely does nothing.
- `Replace All` replaces all matches in one operation.
- Replacement text is literal; `$&`, backreferences, and regular-expression syntax have no special meaning.
- If the query is empty or no match exists, content remains unchanged.
- Replacement may include newlines and Markdown syntax because it operates on the source string.

## Testing

### Unit tests

- Test current-match replacement with case differences and an active index.
- Test replace-all behavior with multiple matches.
- Test empty query, no match, and out-of-range active index as no-ops.
- Test literal replacement text containing regex metacharacters.

### Component/source tests

- Verify FindBar renders replacement controls only when editing.
- Verify App passes the active editing state and handles both replacement events.
- Verify replacement uses `tabs.setContent`, preserving the existing dirty-state behavior.

### Regression verification

- Run the complete frontend test suite.
- Run the complete Python suite because the desktop bridge and packaged workflow must remain unaffected.
- Build the frontend and refresh the Windows source/package assets.
- Manually verify Ctrl+F in viewing mode is find-only, Ctrl+F in Edit mode exposes replacement, Replace affects one match, and Replace All affects all matches.

