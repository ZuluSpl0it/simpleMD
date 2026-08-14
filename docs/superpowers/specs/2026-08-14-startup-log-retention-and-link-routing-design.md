# Startup Log Retention and Link Routing Design

## Goals

1. Keep only the five newest startup trace files in the portable data
   directory.
2. Route links from rendered Markdown according to their destination without
   allowing navigation to replace the Flatnotes application page.

## Startup log retention

After opening the current trace file, remove older `.log` files from
`data/startup-logs` until the current trace and the four newest previous traces
remain. Ordering uses the timestamped startup-log filename, with file
metadata as a fallback if needed.

Retention is best-effort: missing directories, malformed entries, and delete
failures are ignored so diagnostics can never prevent startup. The current
trace file is always preserved while it is being written.

## Link routing

The frontend intercepts clicks from rendered reader and WYSIWYG content:

- `#anchor` links use normal in-document scrolling.
- `http://` and `https://` links call a Python bridge method that opens the
  system browser.
- Relative and absolute local `.md` links call a Python bridge method that
  resolves the link relative to the current Markdown file, validates it, reads
  it, and returns a document payload for a new Flatnotes tab.
- Other local file links open through the system file handler.

The bridge owns filesystem resolution and validation. It rejects missing or
non-Markdown link targets with a user-visible error rather than allowing the
webview to navigate away from the app. Existing in-document behavior stays
inside the current tab.

## Verification

Python tests cover retaining exactly five logs, preserving the active trace,
ignoring cleanup failures, opening web URLs through the browser adapter, and
resolving valid/invalid Markdown links. Frontend tests cover anchor passthrough,
browser routing, local Markdown tab events, and non-Markdown file routing. The
full Python and frontend suites plus a production build must pass.
