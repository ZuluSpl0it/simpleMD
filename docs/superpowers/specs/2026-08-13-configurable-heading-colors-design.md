# Configurable Heading Colors Design

## Goal

Allow Flatnotes users to configure a distinct text color for each Markdown heading level through `settings.json`. Reader and WYSIWYG headings use the configured colors, while Markdown source remains uncolored. Dark and light themes have separate palettes so every heading remains legible against its background.

## Settings format

The optional `heading_colors` object contains complete dark and light palettes:

```json
{
  "heading_colors": {
    "dark": {
      "h1": "#FCA5A5",
      "h2": "#FDBA74",
      "h3": "#FDE68A",
      "h4": "#86EFAC",
      "h5": "#93C5FD",
      "h6": "#C4B5FD"
    },
    "light": {
      "h1": "#B91C1C",
      "h2": "#C2410C",
      "h3": "#A16207",
      "h4": "#15803D",
      "h5": "#1D4ED8",
      "h6": "#6D28D9"
    }
  }
}
```

These values are the defaults when the object or any individual entry is absent.

## Validation and compatibility

Each entry is validated independently. A valid value is a string containing `#` followed by exactly six hexadecimal digits; matching is case-insensitive. A missing or invalid entry falls back to the default for its theme and heading level without discarding valid sibling entries.

Existing settings files remain compatible because `heading_colors` is optional. Saving a workspace or changing the theme must preserve the validated palettes alongside the existing workspace, theme, and font-size settings. Manual changes to `settings.json` take effect the next time Flatnotes starts.

## Backend design

The settings model carries both complete heading palettes. `SettingsStore.load()` produces validated palettes, and its shared save path serializes them with all other settings. A dedicated desktop bridge method returns both palettes to the frontend as a JSON-compatible nested object.

Keeping palette loading and validation in Python provides one canonical settings interpretation. The frontend receives complete, trusted values and does not need to duplicate fallback rules.

## Frontend design

At startup, the app loads both palettes and retains them in memory. A small application function applies the active theme's six colors to these root CSS variables:

```css
--flatnotes-h1-color
--flatnotes-h2-color
--flatnotes-h3-color
--flatnotes-h4-color
--flatnotes-h5-color
--flatnotes-h6-color
```

The same function runs after the user toggles between dark and light mode, so heading colors change immediately without restarting.

Only these selectors consume the variables:

- Reader `.toastui-editor-contents h1` through `h6`
- WYSIWYG `.toastui-editor-ww-container .toastui-editor-contents h1` through `h6`

Markdown editor source tokens and the heading picker retain their current styling. The color applies only to heading text; H1 and H2 underline borders remain neutral.

## Failure handling

If the bridge call fails, the frontend uses the same built-in default palettes so the document remains readable. An invalid individual setting never prevents startup and never affects other valid colors. This feature adds no settings UI, file watcher, or live reload behavior.

## Testing

Backend tests verify:

- Default dark and light palettes
- Acceptance of valid six-digit hex values
- Per-entry fallback for missing, malformed, or non-string values
- Palette preservation when saving a workspace or theme
- Complete bridge payloads with and without a settings store

Frontend tests verify:

- Startup requests both palettes and applies the active theme
- Theme toggling reapplies the corresponding palette
- Six CSS variables drive reader and WYSIWYG heading text
- Markdown source heading styling does not consume the color variables
- H1 and H2 border colors are not tied to heading color variables

## Out of scope

- In-app color pickers or settings screens
- Live reloading after external edits to `settings.json`
- Alpha or shorthand hex formats
- Coloring Markdown source or the heading picker
- Coloring H1/H2 borders
