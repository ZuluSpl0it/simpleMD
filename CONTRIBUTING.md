# Contributing to simpleMD

Thank you for your interest in simpleMD.

simpleMD is an independent project based on the MIT-licensed
[Flatnotes](https://github.com/dullage/flatnotes) codebase. Contributions
should keep the application portable, predictable, and focused on working with
ordinary Markdown files.

## Project principles

- Keep notes in user-controlled Markdown files.
- Avoid unnecessary databases, lock-in, and heavyweight startup work.
- Preserve compatibility with existing workspaces and configuration where
  practical.
- Keep the desktop shell responsive and make failures diagnosable.

## Before submitting changes

1. Explain the user-visible problem and the smallest useful solution.
2. Add or update tests for behavior that can be tested automatically.
3. Run the relevant Python and frontend test suites.
4. Update documentation when behavior, packaging, or configuration changes.

Please avoid renaming compatibility-sensitive identifiers such as
`FLATNOTES_*` environment variables or the internal `flatnotes_desktop`
Python package without a migration plan.

## Pull requests and issues

Issues and pull requests are welcome. Please include reproducible steps for
bugs, the operating system and build type involved, and relevant startup or
application logs. Keep pull requests focused so they can be reviewed and
tested independently.

## Attribution

Changes in this repository build on the original Flatnotes project. Please
retain the MIT license and attribution when copying or substantially reusing
code from that project.
