# Configurable Typography Design

## Goal

Replace Flatnotes' scalar paragraph and code font settings with one structured
`font_size` setting. It supplies a base text size, a code size, and an
independent multiplier for each heading level.

## Settings format

New and default portable settings use this shape:

```json
"font_size": {
  "heading_multiplier": {
    "h1": 2.4,
    "h2": 2.08,
    "h3": 1.78,
    "h4": 1.5,
    "h5": 1.29,
    "h6": 1.15
  },
  "text": 14,
  "code": 12
}
```

At the defaults, the effective heading sizes are approximately 33.6, 29.12,
24.92, 21, 18.06, and 16.1 pixels. Fractional CSS font sizes are intentional:
the browser renders them smoothly, and `text` can scale the full heading
hierarchy without rounding jumps.

## Backend behavior

- The Python settings model owns a canonical default typography dictionary and
  returns a copy for every setting instance.
- Each setting validates independently. `text` and `code` must be integers
  from 8 through 72; each heading multiplier must be a finite number from 0.5
  through 4. Invalid or absent entries use only that entry's default.
- The settings store accepts the legacy numeric `font_size` plus
  `code_font_size` form. It maps that legacy value to the previous heading
  multipliers so existing installations retain their current appearance.
- On the next workspace or theme save, legacy settings serialize in the new
  object form. The former top-level `code_font_size` key is no longer written.
- The desktop bridge returns the complete typography object, including when no
  settings store is available.

## Frontend behavior

- The browser receives the object at startup and applies `text`, `code`, and
  six heading multipliers as root CSS custom properties.
- Reader, Markdown source, and WYSIWYG editor use the same base text/code
  variables. Each heading uses `calc(text * its multiplier)` in its existing
  selector, keeping the current styling structure intact.
- No typography controls are added to the application UI. Changes in
  `settings.json` apply on the next application start.

## Compatibility and verification

- A scalar `"font_size": 34` is legacy input, not the new default setting
  format. It means 34px text and is migrated to the object form on the next
  save; the defaults are used only when the object is omitted or individual
  object entries are missing/invalid.
- Tests cover defaults, partial validation, legacy loading/migration, bridge
  payloads, browser CSS-variable application, and typography selectors in all
  editor modes.
- After tests and production build pass, sync the source and built assets to
  `C:\src`, including the portable package's WebView2 assets.
