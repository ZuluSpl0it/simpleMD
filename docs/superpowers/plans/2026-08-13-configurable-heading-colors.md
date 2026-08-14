# Configurable Heading Colors Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load separate dark and light H1–H6 color palettes from `settings.json` and apply them to heading text in reader and WYSIWYG views only.

**Architecture:** Python owns palette defaults, per-entry validation, persistence, and the pywebview bridge payload. A focused frontend module owns browser-side defaults and maps the active palette to six root CSS variables. Existing reader and WYSIWYG selectors consume those variables; Markdown source and heading borders remain unchanged.

**Tech Stack:** Python 3.13, dataclasses, JSON, pytest, pywebview bridge, Vue 3, JavaScript, CSS custom properties, Vitest, Vite

---

## File map

- Modify `desktop/src/flatnotes_desktop/models.py`: canonical Python defaults and the settings model field.
- Modify `desktop/src/flatnotes_desktop/settings.py`: per-entry hex validation and palette persistence.
- Modify `desktop/tests/test_settings.py`: settings defaults, partial validation, and save-preservation coverage.
- Modify `desktop/src/flatnotes_desktop/bridge.py`: expose complete palettes to JavaScript.
- Modify `desktop/tests/test_bridge.py`: bridge payload and no-store fallback coverage.
- Modify `desktop/client/src/api/desktop.js`: add the heading-color bridge call.
- Create `desktop/client/src/headingColors.js`: frontend defaults and CSS-variable application.
- Create `desktop/client/src/heading-colors.test.js`: unit and integration-source coverage.
- Modify `desktop/client/src/App.vue`: load palettes and reapply them when the theme changes.
- Modify `desktop/client/src/style.css`: default variables and rendered-heading text colors.
- Modify `desktop/client/src/style.test.js`: enforce reader/WYSIWYG scope and neutral Markdown/borders.

**Execution precondition:** Run `git status --short` before Task 1. If the worktree is dirty, do not stage anything from this plan until the main agent has either committed the existing verified work as its own baseline or supplied a clean worktree containing that baseline. The task commits below intentionally stage complete files; running them over unrelated unstaged changes would mix features.

### Task 1: Add validated heading palettes to settings

**Files:**
- Modify: `desktop/src/flatnotes_desktop/models.py`
- Modify: `desktop/src/flatnotes_desktop/settings.py`
- Test: `desktop/tests/test_settings.py`

- [ ] **Step 1: Write failing tests for defaults, partial validation, and persistence**

Add `import json` at the top of `desktop/tests/test_settings.py`, then add:

```python
def test_settings_default_heading_colors(tmp_path):
    from flatnotes_desktop.models import default_heading_colors
    from flatnotes_desktop.settings import SettingsStore

    settings = SettingsStore(tmp_path / "data").load()

    assert settings.heading_colors == default_heading_colors()


def test_settings_validate_and_preserve_heading_colors(tmp_path):
    from flatnotes_desktop.models import default_heading_colors
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        json.dumps(
            {
                "heading_colors": {
                    "dark": {
                        "h1": "#abcdef",
                        "h2": "#12345",
                        "h3": 123456,
                    },
                    "light": {"h6": "#1020A0"},
                }
            }
        ),
        encoding="utf-8",
    )

    defaults = default_heading_colors()
    settings = store.load()

    assert settings.heading_colors["dark"]["h1"] == "#abcdef"
    assert settings.heading_colors["dark"]["h2"] == defaults["dark"]["h2"]
    assert settings.heading_colors["dark"]["h3"] == defaults["dark"]["h3"]
    assert settings.heading_colors["light"]["h6"] == "#1020A0"

    store.save_theme("light")
    store.save_workspace(r"D:\\Notes")

    saved = json.loads(store.path.read_text(encoding="utf-8"))
    assert saved["heading_colors"] == settings.heading_colors
```

- [ ] **Step 2: Run the settings tests and verify the new tests fail**

Run:

```bash
desktop/.venv/bin/python -m pytest desktop/tests/test_settings.py -q
```

Expected: FAIL because `Settings` has no `heading_colors` field and `default_heading_colors` does not exist.

- [ ] **Step 3: Define canonical defaults and a safe clone function**

Update the imports and add the palette definitions before `Settings` in `desktop/src/flatnotes_desktop/models.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_HEADING_COLORS = {
    "dark": {
      "h1": "#93C5FD",
      "h2": "#C4B5FD",
      "h3": "#86EFAC",
      "h4": "#FDE68A",
      "h5": "#FDBA74",
      "h6": "#FCA5A5"
    },
    "light": {
      "h1": "#1D4ED8",
      "h2": "#6D28D9",
      "h3": "#15803D",
      "h4": "#A16207",
      "h5": "#E94C0E",
      "h6": "#C20C0C"
    }
}


def default_heading_colors() -> dict[str, dict[str, str]]:
    return {theme: dict(palette) for theme, palette in DEFAULT_HEADING_COLORS.items()}
```

Extend `Settings`:

```python
@dataclass(frozen=True)
class Settings:
    workspace: str | None = None
    theme: str = "dark"
    font_size: int = 17
    code_font_size: int = 13
    heading_colors: dict[str, dict[str, str]] = field(
        default_factory=default_heading_colors
    )
```

- [ ] **Step 4: Load, validate, and persist every palette entry**

In `desktop/src/flatnotes_desktop/settings.py`, import `re` and `default_heading_colors`:

```python
import json
import os
import re
from pathlib import Path

from .models import Settings, default_heading_colors
```

Add the heading levels to `SettingsStore`:

```python
    HEADING_LEVELS = tuple(f"h{level}" for level in range(1, 7))
```

Pass the loaded JSON value into `Settings`:

```python
            heading_colors=self._heading_colors(payload.get("heading_colors")),
```

Add this validator after `_font_size`:

```python
    @classmethod
    def _heading_colors(cls, value) -> dict[str, dict[str, str]]:
        colors = default_heading_colors()
        if not isinstance(value, dict):
            return colors
        for theme in ("dark", "light"):
            palette = value.get(theme)
            if not isinstance(palette, dict):
                continue
            for heading in cls.HEADING_LEVELS:
                color = palette.get(heading)
                if isinstance(color, str) and re.fullmatch(
                    r"#[0-9A-Fa-f]{6}", color
                ):
                    colors[theme][heading] = color
        return colors
```

Replace the two save methods with:

```python
    def save_workspace(self, workspace: str | None) -> Settings:
        current = self.load()
        return self._save(
            workspace=workspace,
            theme=current.theme,
            font_size=current.font_size,
            code_font_size=current.code_font_size,
            heading_colors=current.heading_colors,
        )

    def save_theme(self, theme: str) -> Settings:
        if theme not in {"dark", "light"}:
            raise ValueError("Theme must be 'dark' or 'light'.")
        current = self.load()
        return self._save(
            workspace=current.workspace,
            theme=theme,
            font_size=current.font_size,
            code_font_size=current.code_font_size,
            heading_colors=current.heading_colors,
        )
```

Replace `_save()` with:

```python
    def _save(
        self,
        *,
        workspace: str | None,
        theme: str,
        font_size: int,
        code_font_size: int,
        heading_colors: dict[str, dict[str, str]],
    ) -> Settings:
        self.data_directory.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "workspace": workspace,
                    "theme": theme,
                    "font_size": font_size,
                    "code_font_size": code_font_size,
                    "heading_colors": heading_colors,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
        return Settings(
            workspace=workspace,
            theme=theme,
            font_size=font_size,
            code_font_size=code_font_size,
            heading_colors={
                theme: dict(palette) for theme, palette in heading_colors.items()
            },
        )
```

- [ ] **Step 5: Run settings tests and the full Python suite**

Run:

```bash
desktop/.venv/bin/python -m pytest desktop/tests/test_settings.py -q
desktop/.venv/bin/python -m pytest desktop/tests -q
```

Expected: all settings tests pass, followed by the complete Python suite passing.

- [ ] **Step 6: Commit the settings layer**

```bash
git add desktop/src/flatnotes_desktop/models.py desktop/src/flatnotes_desktop/settings.py desktop/tests/test_settings.py
git commit -m "feat: validate configurable heading palettes"
```

### Task 2: Expose palettes through the desktop bridge

**Files:**
- Modify: `desktop/src/flatnotes_desktop/bridge.py`
- Test: `desktop/tests/test_bridge.py`

- [ ] **Step 1: Write failing bridge tests**

Add to `desktop/tests/test_bridge.py`:

```python
def test_bridge_reads_heading_colors(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"heading_colors":{"dark":{"h1":"#010203"},'
        '"light":{"h6":"#A0B0C0"}}}',
        encoding="utf-8",
    )
    bridge = DesktopBridge(None, FileService(), settings=store)

    colors = bridge.get_heading_colors()

    assert colors["dark"]["h1"] == "#010203"
    assert colors["light"]["h6"] == "#A0B0C0"
    assert set(colors["dark"]) == {f"h{level}" for level in range(1, 7)}


def test_bridge_heading_colors_fall_back_without_settings():
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.models import default_heading_colors

    bridge = DesktopBridge(None, FileService())

    assert bridge.get_heading_colors() == default_heading_colors()
```

- [ ] **Step 2: Run the bridge tests and verify failure**

Run:

```bash
desktop/.venv/bin/python -m pytest desktop/tests/test_bridge.py -q
```

Expected: FAIL with `AttributeError: 'DesktopBridge' object has no attribute 'get_heading_colors'`.

- [ ] **Step 3: Implement the bridge method**

Import the clone helper in `desktop/src/flatnotes_desktop/bridge.py`:

```python
from .models import default_heading_colors
```

Add after `get_font_settings()`:

```python
    def get_heading_colors(self) -> dict[str, dict[str, str]]:
        if self.settings is None:
            return default_heading_colors()
        colors = self.settings.load().heading_colors
        return {theme: dict(palette) for theme, palette in colors.items()}
```

- [ ] **Step 4: Run bridge tests and the full Python suite**

Run:

```bash
desktop/.venv/bin/python -m pytest desktop/tests/test_bridge.py -q
desktop/.venv/bin/python -m pytest desktop/tests -q
```

Expected: both commands pass.

- [ ] **Step 5: Commit the bridge**

```bash
git add desktop/src/flatnotes_desktop/bridge.py desktop/tests/test_bridge.py
git commit -m "feat: expose heading palettes to desktop frontend"
```

### Task 3: Build a focused frontend palette applicator

**Files:**
- Create: `desktop/client/src/headingColors.js`
- Create: `desktop/client/src/heading-colors.test.js`

- [ ] **Step 1: Write failing unit tests for theme selection and fallback**

Create `desktop/client/src/heading-colors.test.js`:

```javascript
import { describe, expect, it, vi } from "vitest";
import {
  applyHeadingColors,
  DEFAULT_HEADING_COLORS,
} from "./headingColors.js";

function fakeRoot() {
  const values = {};
  return {
    values,
    style: {
      setProperty: vi.fn((name, value) => { values[name] = value; }),
    },
  };
}

describe("heading colors", () => {
  it("applies all six values from the active theme", () => {
    const root = fakeRoot();
    const colors = structuredClone(DEFAULT_HEADING_COLORS);
    colors.light.h1 = "#010203";
    colors.light.h6 = "#A0B0C0";

    applyHeadingColors(root, colors, "light");

    expect(root.values["--flatnotes-h1-color"]).toBe("#010203");
    expect(root.values["--flatnotes-h6-color"]).toBe("#A0B0C0");
    expect(root.style.setProperty).toHaveBeenCalledTimes(6);
  });

  it("uses frontend defaults when the bridge payload is unavailable", () => {
    const root = fakeRoot();

    applyHeadingColors(root, null, "dark");

    expect(root.values["--flatnotes-h1-color"]).toBe(
      DEFAULT_HEADING_COLORS.dark.h1,
    );
    expect(root.values["--flatnotes-h6-color"]).toBe(
      DEFAULT_HEADING_COLORS.dark.h6,
    );
  });

  it("falls back per entry for a malformed frontend payload", () => {
    const root = fakeRoot();

    applyHeadingColors(root, { dark: { h1: "red", h2: "#112233" } }, "dark");

    expect(root.values["--flatnotes-h1-color"]).toBe(
      DEFAULT_HEADING_COLORS.dark.h1,
    );
    expect(root.values["--flatnotes-h2-color"]).toBe("#112233");
  });
});
```

- [ ] **Step 2: Run the new test and verify it fails**

Run:

```bash
npm test -- --run src/heading-colors.test.js
```

Working directory: `desktop/client`

Expected: FAIL because `headingColors.js` does not exist.

- [ ] **Step 3: Implement the palette applicator**

Create `desktop/client/src/headingColors.js`:

```javascript
const levels = ["h1", "h2", "h3", "h4", "h5", "h6"];

export const DEFAULT_HEADING_COLORS = Object.freeze({
  dark: Object.freeze({
    h1: "#FCA5A5",
    h2: "#FDBA74",
    h3: "#FDE68A",
    h4: "#86EFAC",
    h5: "#93C5FD",
    h6: "#C4B5FD",
  }),
  light: Object.freeze({
    h1: "#B91C1C",
    h2: "#C2410C",
    h3: "#A16207",
    h4: "#15803D",
    h5: "#1D4ED8",
    h6: "#6D28D9",
  }),
});

function validColor(value) {
  return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);
}

export function applyHeadingColors(root, colors, theme) {
  const activeTheme = theme === "light" ? "light" : "dark";
  const defaults = DEFAULT_HEADING_COLORS[activeTheme];
  const palette = colors?.[activeTheme];
  for (const level of levels) {
    const candidate = palette?.[level];
    root.style.setProperty(
      `--flatnotes-${level}-color`,
      validColor(candidate) ? candidate : defaults[level],
    );
  }
}
```

- [ ] **Step 4: Run the unit tests**

Run:

```bash
npm test -- --run src/heading-colors.test.js
```

Working directory: `desktop/client`

Expected: 3 tests pass.

- [ ] **Step 5: Commit the frontend helper**

```bash
git add desktop/client/src/headingColors.js desktop/client/src/heading-colors.test.js
git commit -m "feat: add heading palette applicator"
```

### Task 4: Load and switch palettes in the Vue application

**Files:**
- Modify: `desktop/client/src/api/desktop.js`
- Modify: `desktop/client/src/App.vue`
- Modify: `desktop/client/src/heading-colors.test.js`

- [ ] **Step 1: Add a failing integration-source test**

Append to `desktop/client/src/heading-colors.test.js`:

```javascript
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

it("loads palettes at startup and reapplies them on theme changes", () => {
  const app = readFileSync(
    fileURLToPath(new URL("./App.vue", import.meta.url)),
    "utf8",
  );
  const api = readFileSync(
    fileURLToPath(new URL("./api/desktop.js", import.meta.url)),
    "utf8",
  );

  expect(api).toMatch(/getHeadingColors.*get_heading_colors/);
  expect(app).toMatch(/getHeadingColors/);
  expect(app).toMatch(/headingColors\.value\s*=\s*await getHeadingColors\(\)\.catch/);
  expect(app.match(/applyHeadingColors\(/g)).toHaveLength(2);
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
npm test -- --run src/heading-colors.test.js
```

Working directory: `desktop/client`

Expected: FAIL because the API and application do not reference `getHeadingColors`.

- [ ] **Step 3: Add the desktop API call**

Append to `desktop/client/src/api/desktop.js`:

```javascript
export const getHeadingColors = () => call("get_heading_colors");
```

- [ ] **Step 4: Load and apply palettes in `App.vue`**

Add `getHeadingColors` to the existing desktop API import. Add this import:

```javascript
import {
  applyHeadingColors,
  DEFAULT_HEADING_COLORS,
} from "./headingColors.js";
```

Add state beside `theme`:

```javascript
const headingColors = ref(DEFAULT_HEADING_COLORS);
```

Extend `toggleTheme()` after setting `document.documentElement.dataset.theme`:

```javascript
  applyHeadingColors(
    document.documentElement,
    headingColors.value,
    theme.value,
  );
```

In `onMounted()`, after loading and applying the theme and before reading the workspace, load the palettes and apply them:

```javascript
  headingColors.value = await getHeadingColors().catch(
    () => DEFAULT_HEADING_COLORS,
  );
  applyHeadingColors(
    document.documentElement,
    headingColors.value,
    theme.value,
  );
```

- [ ] **Step 5: Run focused and full frontend tests**

Run:

```bash
npm test -- --run src/heading-colors.test.js
npm test -- --run
```

Working directory: `desktop/client`

Expected: the focused tests and full frontend suite pass.

- [ ] **Step 6: Commit the application integration**

```bash
git add desktop/client/src/api/desktop.js desktop/client/src/App.vue desktop/client/src/heading-colors.test.js
git commit -m "feat: apply theme-specific heading palettes"
```

### Task 5: Color rendered headings without changing Markdown source or borders

**Files:**
- Modify: `desktop/client/src/style.css`
- Modify: `desktop/client/src/style.test.js`

- [ ] **Step 1: Write failing CSS-scope tests**

Add to `desktop/client/src/style.test.js`:

```javascript
it("colors headings only in reader and WYSIWYG views", () => {
  const css = readFileSync(stylePath, "utf8");

  for (let level = 1; level <= 6; level += 1) {
    expect(css).toMatch(new RegExp(
      `\\.editor\\.viewing\\s+\\.toastui-editor-contents\\s+h${level}\\s*\\{[^}]*color:\\s*var\\(--flatnotes-h${level}-color\\)`,
    ));
    expect(css).toMatch(new RegExp(
      `\\.toastui-editor-ww-container\\s+\\.toastui-editor-contents\\s+h${level}\\s*\\{[^}]*color:\\s*var\\(--flatnotes-h${level}-color\\)`,
    ));
  }

  expect(css).not.toMatch(/markdown-only[^}]*--flatnotes-h[1-6]-color/);
  expect(css).not.toMatch(/border[^;}]*var\(--flatnotes-h[1-6]-color\)/);
});
```

- [ ] **Step 2: Run the style test and verify it fails**

Run:

```bash
npm test -- --run src/style.test.js
```

Working directory: `desktop/client`

Expected: FAIL because the rendered heading rules do not use heading-color variables.

- [ ] **Step 3: Define safe CSS defaults for both themes**

Add the dark variables to the existing `:root` block in `desktop/client/src/style.css`:

```css
  --flatnotes-h1-color: #FCA5A5;
  --flatnotes-h2-color: #FDBA74;
  --flatnotes-h3-color: #FDE68A;
  --flatnotes-h4-color: #86EFAC;
  --flatnotes-h5-color: #93C5FD;
  --flatnotes-h6-color: #C4B5FD;
```

Add the light variables to `:root[data-theme="light"]`:

```css
  --flatnotes-h1-color: #B91C1C;
  --flatnotes-h2-color: #C2410C;
  --flatnotes-h3-color: #A16207;
  --flatnotes-h4-color: #15803D;
  --flatnotes-h5-color: #1D4ED8;
  --flatnotes-h6-color: #6D28D9;
```

- [ ] **Step 4: Apply variables to reader and WYSIWYG text only**

Replace the existing reader H1–H6 declarations with:

```css
.editor.viewing .toastui-editor-contents h1 {
  color: var(--flatnotes-h1-color);
  font-size: calc(var(--flatnotes-font-size) * 2);
  line-height: 1.2;
}
.editor.viewing .toastui-editor-contents h2 {
  color: var(--flatnotes-h2-color);
  font-size: calc(var(--flatnotes-font-size) * 1.7059);
  line-height: 1.25;
}
.editor.viewing .toastui-editor-contents h3 {
  color: var(--flatnotes-h3-color);
  font-size: calc(var(--flatnotes-font-size) * 1.4706);
  line-height: 1.3;
}
.editor.viewing .toastui-editor-contents h4 {
  color: var(--flatnotes-h4-color);
  font-size: calc(var(--flatnotes-font-size) * 1.2353);
  line-height: 1.35;
}
.editor.viewing .toastui-editor-contents h5 {
  color: var(--flatnotes-h5-color);
  font-size: calc(var(--flatnotes-font-size) * 1.0588);
  line-height: 1.4;
}
.editor.viewing .toastui-editor-contents h6 {
  color: var(--flatnotes-h6-color);
  font-size: calc(var(--flatnotes-font-size) * .9412);
  line-height: 1.45;
}
```

Replace the existing WYSIWYG H1–H6 declarations with:

```css
.editor-shell.editing .editor .toastui-editor-ww-container .toastui-editor-contents h1 {
  color: var(--flatnotes-h1-color);
  font-size: calc(var(--flatnotes-font-size) * 2);
  line-height: 1.2;
}
.editor-shell.editing .editor .toastui-editor-ww-container .toastui-editor-contents h2 {
  color: var(--flatnotes-h2-color);
  font-size: calc(var(--flatnotes-font-size) * 1.7059);
  line-height: 1.25;
}
.editor-shell.editing .editor .toastui-editor-ww-container .toastui-editor-contents h3 {
  color: var(--flatnotes-h3-color);
  font-size: calc(var(--flatnotes-font-size) * 1.4706);
  line-height: 1.3;
}
.editor-shell.editing .editor .toastui-editor-ww-container .toastui-editor-contents h4 {
  color: var(--flatnotes-h4-color);
  font-size: calc(var(--flatnotes-font-size) * 1.2353);
  line-height: 1.35;
}
.editor-shell.editing .editor .toastui-editor-ww-container .toastui-editor-contents h5 {
  color: var(--flatnotes-h5-color);
  font-size: calc(var(--flatnotes-font-size) * 1.0588);
  line-height: 1.4;
}
.editor-shell.editing .editor .toastui-editor-ww-container .toastui-editor-contents h6 {
  color: var(--flatnotes-h6-color);
  font-size: calc(var(--flatnotes-font-size) * .9412);
  line-height: 1.45;
}
```

Do not change any `.markdown-only`, `.toastui-editor-md-heading*`, `border`, or heading-picker declaration.

- [ ] **Step 5: Run style tests and the full frontend suite**

Run:

```bash
npm test -- --run src/style.test.js
npm test -- --run
npm run build
```

Working directory: `desktop/client`

Expected: all tests pass and Vite produces `desktop/client/dist/index.html` plus hashed assets.

- [ ] **Step 6: Commit rendered heading styles**

```bash
git add desktop/client/src/style.css desktop/client/src/style.test.js
git commit -m "feat: color rendered heading levels"
```

### Task 6: Verify the complete feature and synchronize Windows sources

**Files:**
- Verify: all files above
- Synchronize: `desktop/client/src` to `C:\src\client\src`
- Synchronize: `desktop/client/dist` to `C:\src\client\dist`
- Synchronize: packaged assets to `C:\src\dist\Flatnotes\_internal\flatnotes_desktop\assets`
- Synchronize: Python source/tests under `desktop/src` and `desktop/tests` to their `C:\src` counterparts

- [ ] **Step 1: Run fresh backend and frontend verification**

From the worktree root:

```bash
desktop/.venv/bin/python -m pytest desktop/tests -q
npm --prefix desktop/client test -- --run
npm --prefix desktop/client run build
git diff --check
```

Expected: Python and frontend suites pass, Vite completes successfully, and `git diff --check` prints nothing.

- [ ] **Step 2: Inspect the effective settings payload manually**

Create or update the portable app's `data/settings.json` with one unmistakable test override, for example dark H1 `#00FF00`, while retaining the other entries. Start Flatnotes, open a document containing H1–H6, and verify:

- Reader H1 uses `#00FF00`.
- WYSIWYG H1 uses `#00FF00`.
- Markdown source heading text keeps its current color.
- Switching to light mode swaps to the light palette immediately.
- H1/H2 underline borders remain neutral.

Restore the desired H1 value after this check.

- [ ] **Step 3: Synchronize the verified source and bundle to `C:\src`**

From WSL:

```bash
cp -r desktop/client/src/. /mnt/c/src/client/src/
cp -r desktop/client/dist/. /mnt/c/src/client/dist/
cp -r desktop/src/. /mnt/c/src/src/
cp desktop/tests/*.py /mnt/c/src/tests/
cp -r desktop/client/dist/. /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/
```

If Flatnotes is running, close it before testing the packaged copy so WebView2 loads the new hashed assets.

- [ ] **Step 4: Verify the Windows mirror and packaged asset entry point**

Run:

```bash
diff -qr desktop/client/src /mnt/c/src/client/src
diff -q desktop/client/dist/index.html /mnt/c/src/client/dist/index.html
diff -q desktop/client/dist/index.html /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/index.html
cat /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/index.html
```

Expected: the diff commands print nothing, and packaged `index.html` references the newest hashed JavaScript and CSS assets.

- [ ] **Step 5: Review commits and working tree**

```bash
git log -5 --oneline
git status --short
```

Expected: the heading-color implementation is represented by the focused task commits, with no untracked feature files or unstaged heading-color changes.
