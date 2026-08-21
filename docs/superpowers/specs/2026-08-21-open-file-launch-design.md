# Open Markdown Files From Windows Launch Design

## Goal

Opening a `.md` file through Windows “Open with simpleMD” opens that file in a tab.

## Design

The desktop entry point will pass process arguments into `run()`. Startup will select existing command-line arguments whose paths are regular Markdown files, then expose them to the frontend after mount through the existing `open_dropped_path` bridge. The frontend will open each returned document in order. A launch with no valid files keeps the current home-screen behavior.

This change does not add single-instance IPC; repeated launches remain separate processes.

## Verification

Add focused Python tests for command-line filtering and run the desktop app test module. No broad end-to-end testing required.
