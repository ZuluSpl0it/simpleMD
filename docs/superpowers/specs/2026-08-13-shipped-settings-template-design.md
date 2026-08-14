# Shipped Settings Template Design

## Goal

Track Flatnotes' portable default settings in the repository and include them
in newly built Windows distributions without overwriting existing user
settings.

## Template

Add `desktop/default-data/settings.json` to version control. It contains:

- the dark theme;
- the default `font_size` typography object with 14px text, 12px code, and
  the configured H1–H6 multipliers;
- the current custom dark and light heading-color palettes.

The template intentionally has no `workspace` value. On its first start, a
portable app creates and saves its own `workspace` directory beside the
executable, rather than trying to open the development-only `C:\src` path.

## Build behavior

`desktop/scripts/build_windows.ps1` copies the template to
`dist\Flatnotes\data\settings.json` only when that destination does not
already exist. This makes the template part of a fresh distributable while
preserving a user's selected workspace, theme, typography, heading colors,
and other data when the application is rebuilt in place.

## Verification

Tests verify the tracked template is valid JSON, has no workspace key, and
contains the intended typography and heading palettes. The build script test
or source assertion verifies its non-overwriting copy condition. The final
Windows synchronization copies the template and build-script changes to
`C:\src`; a Windows rebuild then produces a fresh portable folder with the
default settings file.
