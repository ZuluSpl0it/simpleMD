# Configurable Typography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace scalar font settings with a validated typography object containing text, code, and heading multiplier values.

**Architecture:** Python owns default typography values, per-entry validation, legacy scalar migration, persistence, and the pywebview payload. A frontend helper validates the browser payload and maps it to root CSS variables. Reader, Markdown source, and WYSIWYG retain their existing selectors while calculating heading sizes from text and per-level multipliers.

**Tech Stack:** Python 3.13, dataclasses, JSON, pytest, pywebview, Vue 3, JavaScript, CSS custom properties, Vitest, Vite.

---

## File map

- Modify desktop/src/flatnotes_desktop/models.py: defaults and Settings field.
- Modify desktop/src/flatnotes_desktop/settings.py: validation, migration, persistence.
- Modify desktop/tests/test_settings.py: defaults, partial fallback, migration.
- Modify desktop/src/flatnotes_desktop/bridge.py and desktop/tests/test_bridge.py: structured bridge payload.
- Create desktop/client/src/fontSettings.js: fallback and CSS-variable mapping.
- Modify desktop/client/src/font-settings.test.js and App.vue: frontend behavior.
- Modify desktop/client/src/style.css and style.test.js: rendered typography.
- Synchronize sources and built assets to C:\src.

### Task 1: Store validated typography settings

**Files:**
- Modify: desktop/src/flatnotes_desktop/models.py
- Modify: desktop/src/flatnotes_desktop/settings.py
- Test: desktop/tests/test_settings.py

- [ ] **Step 1: Write failing settings tests**

Replace scalar-font tests with:

~~~python
def test_settings_default_font_sizes(tmp_path):
    from flatnotes_desktop.models import default_font_sizes
    from flatnotes_desktop.settings import SettingsStore

    assert SettingsStore(tmp_path / "data").load().font_size == default_font_sizes()


def test_settings_validates_font_size_entries_independently(tmp_path):
    from flatnotes_desktop.models import default_font_sizes
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"font_size":{"text":18,"code":"large",'
        '"heading_multiplier":{"h1":2.5,"h2":0,"h3":"large"}}}',
        encoding="utf-8",
    )

    defaults = default_font_sizes()
    sizes = store.load().font_size

    assert sizes["text"] == 18
    assert sizes["code"] == defaults["code"]
    assert sizes["heading_multiplier"]["h1"] == 2.5
    assert sizes["heading_multiplier"]["h2"] == defaults["heading_multiplier"]["h2"]
    assert sizes["heading_multiplier"]["h3"] == defaults["heading_multiplier"]["h3"]


def test_legacy_font_sizes_are_preserved_and_migrated_on_save(tmp_path):
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text('{"font_size":17,"code_font_size":13}', encoding="utf-8")

    sizes = store.load().font_size
    assert sizes == {
        "text": 17,
        "code": 13,
        "heading_multiplier": {
            "h1": 2.0, "h2": 1.7059, "h3": 1.4706,
            "h4": 1.2353, "h5": 1.0588, "h6": 0.9412,
        },
    }

    store.save_theme("light")
    saved = json.loads(store.path.read_text(encoding="utf-8"))
    assert saved["font_size"] == sizes
    assert "code_font_size" not in saved
~~~

- [ ] **Step 2: Run the tests to verify RED**

~~~bash
desktop/.venv/bin/python -m pytest desktop/tests/test_settings.py -q
~~~

Expected: FAIL because default_font_sizes does not exist and font_size is scalar.

- [ ] **Step 3: Add canonical defaults and migration helpers**

Add to models.py before Settings:

~~~python
DEFAULT_FONT_SIZES = {
    "text": 14,
    "code": 12,
    "heading_multiplier": {
        "h1": 2.4, "h2": 2.08, "h3": 1.78,
        "h4": 1.5, "h5": 1.29, "h6": 1.15,
    },
}


def default_font_sizes() -> dict[str, int | dict[str, float]]:
    return {
        "text": DEFAULT_FONT_SIZES["text"],
        "code": DEFAULT_FONT_SIZES["code"],
        "heading_multiplier": dict(DEFAULT_FONT_SIZES["heading_multiplier"]),
    }
~~~

Replace scalar fields on Settings with:

~~~python
    font_size: dict[str, int | dict[str, float]] = field(
        default_factory=default_font_sizes
    )
~~~

In settings.py import math and default_font_sizes. Define:

~~~python
    PIXEL_SIZE_RANGE = range(8, 73)
    HEADING_MULTIPLIER_RANGE = (0.5, 4.0)
    LEGACY_HEADING_MULTIPLIERS = {
        "h1": 2.0, "h2": 1.7059, "h3": 1.4706,
        "h4": 1.2353, "h5": 1.0588, "h6": 0.9412,
    }
~~~

Call _font_sizes(payload.get("font_size"), payload.get("code_font_size")) from load. Implement:

~~~python
    @classmethod
    def _pixel_size(cls, value, default: int) -> int:
        if isinstance(value, int) and not isinstance(value, bool) and value in cls.PIXEL_SIZE_RANGE:
            return value
        return default

    @classmethod
    def _multiplier(cls, value, default: float) -> float:
        if (
            isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value)
            and cls.HEADING_MULTIPLIER_RANGE[0] <= value <= cls.HEADING_MULTIPLIER_RANGE[1]
        ):
            return float(value)
        return default

    @classmethod
    def _font_sizes(cls, value, legacy_code_size):
        defaults = default_font_sizes()
        if isinstance(value, int) and not isinstance(value, bool):
            return {
                "text": cls._pixel_size(value, defaults["text"]),
                "code": cls._pixel_size(legacy_code_size, 13),
                "heading_multiplier": dict(cls.LEGACY_HEADING_MULTIPLIERS),
            }
        if not isinstance(value, dict):
            return defaults
        multipliers = value.get("heading_multiplier")
        return {
            "text": cls._pixel_size(value.get("text"), defaults["text"]),
            "code": cls._pixel_size(value.get("code"), defaults["code"]),
            "heading_multiplier": {
                heading: cls._multiplier(
                    multipliers.get(heading) if isinstance(multipliers, dict) else None,
                    defaults["heading_multiplier"][heading],
                )
                for heading in cls.HEADING_LEVELS
            },
        }
~~~

Update save_workspace, save_theme, and _save to carry font_size only, write "font_size": font_size, omit code_font_size, and clone the nested object before returning Settings.

- [ ] **Step 4: Verify GREEN and commit**

~~~bash
desktop/.venv/bin/python -m pytest desktop/tests/test_settings.py -q
desktop/.venv/bin/python -m pytest desktop/tests -q
git add desktop/src/flatnotes_desktop/models.py desktop/src/flatnotes_desktop/settings.py desktop/tests/test_settings.py
git commit -m "feat: store configurable typography settings"
~~~

Expected: focused and full backend suites pass before commit.

### Task 2: Expose a safe pywebview typography payload

**Files:**
- Modify: desktop/src/flatnotes_desktop/bridge.py
- Test: desktop/tests/test_bridge.py

- [ ] **Step 1: Write the failing bridge test**

Replace the scalar bridge test with:

~~~python
def test_bridge_reads_font_settings(tmp_path):
    from flatnotes_desktop.bridge import DesktopBridge
    from flatnotes_desktop.files import FileService
    from flatnotes_desktop.settings import SettingsStore

    store = SettingsStore(tmp_path / "data")
    store.data_directory.mkdir(parents=True)
    store.path.write_text(
        '{"font_size":{"text":16,"code":11,'
        '"heading_multiplier":{"h1":2.5}}}',
        encoding="utf-8",
    )

    settings = DesktopBridge(None, FileService(), settings=store).get_font_settings()

    assert settings["text"] == 16
    assert settings["code"] == 11
    assert settings["heading_multiplier"]["h1"] == 2.5
    assert set(settings["heading_multiplier"]) == {f"h{level}" for level in range(1, 7)}
~~~

- [ ] **Step 2: Verify RED**

~~~bash
desktop/.venv/bin/python -m pytest desktop/tests/test_bridge.py -q
~~~

Expected: FAIL because get_font_settings returns scalar-named keys.

- [ ] **Step 3: Return a clone of the object**

Import default_font_sizes in bridge.py and replace the method:

~~~python
    def get_font_settings(self) -> dict[str, int | dict[str, float]]:
        if self.settings is None:
            return default_font_sizes()
        font_size = self.settings.load().font_size
        return {
            "text": font_size["text"],
            "code": font_size["code"],
            "heading_multiplier": dict(font_size["heading_multiplier"]),
        }
~~~

- [ ] **Step 4: Verify GREEN and commit**

~~~bash
desktop/.venv/bin/python -m pytest desktop/tests/test_bridge.py -q
desktop/.venv/bin/python -m pytest desktop/tests -q
git add desktop/src/flatnotes_desktop/bridge.py desktop/tests/test_bridge.py
git commit -m "feat: expose structured typography settings"
~~~

Expected: bridge and full backend suites pass before commit.

### Task 3: Apply safe typography defaults in the browser

**Files:**
- Create: desktop/client/src/fontSettings.js
- Modify: desktop/client/src/font-settings.test.js
- Modify: desktop/client/src/App.vue

- [ ] **Step 1: Write failing browser helper tests**

Replace font-settings.test.js with:

~~~javascript
import { describe, expect, it, vi } from "vitest";
import { applyFontSettings, DEFAULT_FONT_SIZES } from "./fontSettings.js";

function fakeRoot() {
  const values = {};
  return { values, style: { setProperty: vi.fn((name, value) => { values[name] = value; }) } };
}

describe("font settings", () => {
  it("applies text, code, and each heading multiplier", () => {
    const root = fakeRoot();
    applyFontSettings(root, { text: 16, code: 11, heading_multiplier: { h1: 2.5 } });

    expect(root.values["--flatnotes-text-font-size"]).toBe("16px");
    expect(root.values["--flatnotes-code-font-size"]).toBe("11px");
    expect(root.values["--flatnotes-h1-multiplier"]).toBe("2.5");
    expect(root.values["--flatnotes-h6-multiplier"]).toBe(String(DEFAULT_FONT_SIZES.heading_multiplier.h6));
  });

  it("falls back for each malformed browser payload entry", () => {
    const root = fakeRoot();
    applyFontSettings(root, { text: 0, heading_multiplier: { h2: "large" } });

    expect(root.values["--flatnotes-text-font-size"]).toBe(String(DEFAULT_FONT_SIZES.text) + "px");
    expect(root.values["--flatnotes-code-font-size"]).toBe(String(DEFAULT_FONT_SIZES.code) + "px");
    expect(root.values["--flatnotes-h2-multiplier"]).toBe(String(DEFAULT_FONT_SIZES.heading_multiplier.h2));
  });
});
~~~

- [ ] **Step 2: Verify RED**

~~~bash
cd desktop/client && npm test -- --run src/font-settings.test.js
~~~

Expected: FAIL because fontSettings.js does not exist.

- [ ] **Step 3: Implement the helper and startup call**

Create fontSettings.js:

~~~javascript
const levels = ["h1", "h2", "h3", "h4", "h5", "h6"];
export const DEFAULT_FONT_SIZES = Object.freeze({
  text: 14,
  code: 12,
  heading_multiplier: Object.freeze({ h1: 2.4, h2: 2.08, h3: 1.78, h4: 1.5, h5: 1.29, h6: 1.15 }),
});
function pixels(value, fallback) { return Number.isInteger(value) && value >= 8 && value <= 72 ? value : fallback; }
function multiplier(value, fallback) { return typeof value === "number" && Number.isFinite(value) && value >= 0.5 && value <= 4 ? value : fallback; }
export function applyFontSettings(root, settings) {
  root.style.setProperty("--flatnotes-text-font-size", String(pixels(settings?.text, DEFAULT_FONT_SIZES.text)) + "px");
  root.style.setProperty("--flatnotes-code-font-size", String(pixels(settings?.code, DEFAULT_FONT_SIZES.code)) + "px");
  for (const level of levels) {
    root.style.setProperty("--flatnotes-" + level + "-multiplier", String(multiplier(settings?.heading_multiplier?.[level], DEFAULT_FONT_SIZES.heading_multiplier[level])));
  }
}
~~~

In App.vue, import applyFontSettings and DEFAULT_FONT_SIZES. Replace the scalar startup assignments with:

~~~javascript
  const fontSettings = await getFontSettings().catch(() => DEFAULT_FONT_SIZES);
  applyFontSettings(document.documentElement, fontSettings);
~~~

- [ ] **Step 4: Verify GREEN and commit**

~~~bash
cd desktop/client && npm test -- --run src/font-settings.test.js
cd desktop/client && npm test -- --run
git add desktop/client/src/fontSettings.js desktop/client/src/font-settings.test.js desktop/client/src/App.vue
git commit -m "feat: apply configurable typography in the frontend"
~~~

Expected: focused and full frontend suites pass before commit.

### Task 4: Calculate document styles from the typography object

**Files:**
- Modify: desktop/client/src/style.css
- Modify: desktop/client/src/style.test.js

- [ ] **Step 1: Write a failing stylesheet test**

Add this test:

~~~javascript
it("uses configurable text, code, and heading multipliers", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/--flatnotes-text-font-size:\s*14px/);
  expect(css).toMatch(/--flatnotes-code-font-size:\s*12px/);
  for (const level of ["h1", "h2", "h3", "h4", "h5", "h6"]) {
    expect(css).toMatch(new RegExp("--flatnotes-" + level + "-multiplier:"));
    expect(css).toMatch(new RegExp(
      "h" + level.slice(1) + "\\s*\\{[^}]*font-size:\\s*calc\\(\\s*var\\(--flatnotes-text-font-size\\) \\* var\\(--flatnotes-" + level + "-multiplier\\)",
    ));
  }
  expect(css).toMatch(/markdown-only[\s\S]*var\(--flatnotes-text-font-size\)/);
  expect(css).toMatch(/toastui-editor-contents\s+pre\s+code[\s\S]*var\(--flatnotes-code-font-size\)/);
});
~~~

- [ ] **Step 2: Verify RED**

~~~bash
cd desktop/client && npm test -- --run src/style.test.js
~~~

Expected: FAIL because the stylesheet uses 17px, 13px, flatnotes-font-size, and literal heading multipliers.

- [ ] **Step 3: Use exact default variables and configured calculations**

Replace root typography declarations with:

~~~css
  --flatnotes-text-font-size: 14px;
  --flatnotes-code-font-size: 12px;
  --flatnotes-h1-multiplier: 2.4;
  --flatnotes-h2-multiplier: 2.08;
  --flatnotes-h3-multiplier: 1.78;
  --flatnotes-h4-multiplier: 1.5;
  --flatnotes-h5-multiplier: 1.29;
  --flatnotes-h6-multiplier: 1.15;
~~~

Replace every var(--flatnotes-font-size) in reader, Markdown source, and WYSIWYG selectors with var(--flatnotes-text-font-size). Each H1 through H6 selector must use its matching calculation:

~~~css
font-size: calc(
  var(--flatnotes-text-font-size) * var(--flatnotes-h1-multiplier)
);
~~~

Do not change heading colors, heading line heights, underline borders, or fixed heading-picker sizes.

- [ ] **Step 4: Verify GREEN, build, and commit**

~~~bash
cd desktop/client && npm test -- --run src/style.test.js
cd desktop/client && npm test -- --run
cd desktop/client && npm run build
git add desktop/client/src/style.css desktop/client/src/style.test.js
git commit -m "feat: scale headings from configurable typography"
~~~

Expected: focused and full frontend tests pass and Vite emits a new hashed bundle.

### Task 5: Verify and synchronize the portable Windows app

**Files:**
- Verify: all files above
- Synchronize: source, tests, client bundle, and packaged WebView2 assets to C:\src

- [ ] **Step 1: Run complete verification**

~~~bash
desktop/.venv/bin/python -m pytest desktop/tests -q
npm --prefix desktop/client test -- --run
npm --prefix desktop/client run build
git diff --check
~~~

Expected: all test suites, production build, and whitespace check pass.

- [ ] **Step 2: Run a runtime typography smoke test**

Start the built client with a mocked pywebview bridge that returns the default typography payload. Load content with H1 through H6, paragraph text, and a code block. Assert reader and WYSIWYG computed sizes of approximately 33.6, 29.12, 24.92, 21, 18.06, 16.1, 14, and 12 pixels. Assert Markdown source uses text/code variables and the configured heading multiplier selectors.

- [ ] **Step 3: Synchronize verified outputs**

~~~bash
cp -r desktop/client/src/. /mnt/c/src/client/src/
cp -r desktop/client/dist/. /mnt/c/src/client/dist/
cp -r desktop/src/. /mnt/c/src/src/
cp desktop/tests/*.py /mnt/c/src/tests/
cp -r desktop/client/dist/. /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/
~~~

- [ ] **Step 4: Verify the Windows mirror**

~~~bash
diff -qr desktop/client/src /mnt/c/src/client/src
diff -qr desktop/src /mnt/c/src/src
diff -q desktop/client/dist/index.html /mnt/c/src/client/dist/index.html
diff -q desktop/client/dist/index.html /mnt/c/src/dist/Flatnotes/_internal/flatnotes_desktop/assets/index.html
~~~

Expected: no diff output. Restart Flatnotes before opening the packaged copy so WebView2 loads the new hashed assets.
