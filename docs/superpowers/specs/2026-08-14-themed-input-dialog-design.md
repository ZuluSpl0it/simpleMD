# Themed Save and Rename Input Dialogs

## Goal

Replace browser-native JavaScript prompts used for workspace-note save and
rename operations. Native prompts show WebView2's page origin
(`127.0.0.1:<port> says`) and cannot follow Flatnotes' dark/light theme.

## Design

Add one reusable Vue input-dialog component rendered by `App.vue`. It uses the
same modal backdrop and themed surface conventions as `CloseDialog.vue`:

- dark mode uses the existing dark dialog surface;
- light mode uses the existing white surface and dark text;
- the dialog has an accessible dialog role, title, label, text input, and
  Save/Cancel-style actions;
- Enter submits the input and Escape cancels it;
- the input receives focus when the dialog opens.

The component accepts a title, label, initial value, and confirmation label,
then emits `submit(value)` or `cancel`. It does not call the desktop bridge or
own tab state.

## App flow

`App.vue` stores one pending input request with the operation (`save` or
`rename`), title, label, initial value, and confirmation label. `saveActive()`
and `renameActive()` open that request instead of calling `window.prompt()`.
The existing bridge calls run only after the user submits a non-empty value.

Save uses dialog title and action label `Save`; rename uses `Rename`. Delete and
other confirmation dialogs remain unchanged because they already use an
in-app themed dialog or confirmation flow.

## Testing

- Component/source coverage verifies the prompt calls are removed and the
  input dialog is mounted for save and rename.
- Dialog behavior tests cover submit, cancel, Enter, and Escape semantics.
- Existing frontend tests and a real-browser check verify dark/light rendering
  and that Save invokes the same `create_workspace_note` bridge call as before.
