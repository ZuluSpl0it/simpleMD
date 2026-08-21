# WYSIWYG Line Break Repair Design

## Scope

Repair `<br>` handling only. Do not alter Markdown soft breaks or normalize unrelated file content.

## Root Cause

The current `htmlInline` converter directly constructs a Toast UI `widget` ProseMirror node from a CommonMark HTML node. Toast UI expects widget nodes to originate from its widget parser and therefore expects matching custom-inline AST children. The manually constructed node lacks those children. `getWidgetContent()` then dereferences a null child during `setMarkdown()` and mode conversion, aborting the editor mount and leaving WYSIWYG unavailable or blank.

## Design

- Remove the direct `htmlInline`-to-widget converter.
- Represent semantic Markdown `<br>` nodes with a private internal marker before Toast UI converts Markdown to WYSIWYG.
- Configure Toast UI's supported `widgetRules` parser to turn that marker into a real DOM `<br>`.
- Use Toast UI's Markdown AST source positions so only actual HTML break nodes are encoded. Literal `<br>` examples inside inline or fenced code remain text.
- Insert the same valid widget representation when the toolbar button is used in WYSIWYG.
- Normalize widget syntax and the private marker back to `<br>` whenever editor content crosses into application/tab state.
- Decode markers before showing Markdown mode so users continue to see ordinary `<br>` source.
- Prevent the Vue content watcher from feeding normalized emitted content back into Toast UI and corrupting the internal widget representation.

## Verification

- A focused real-browser reproduction must fail against the current implementation and pass after the repair.
- Cover Markdown → WYSIWYG → Markdown preservation, repeated toolbar insertion, consecutive breaks, and literal `<br>` inside code.
- Run the existing frontend unit suite and production build.
- Mirror only corrected source and tests into `C:\src`, then byte-compare the copies.
