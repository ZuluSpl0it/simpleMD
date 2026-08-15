# Desktop Search Capabilities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve desktop workspace search with technical-token matching, accent folding, fuzzy and prefix syntax, relevance boosts, safe phrase queries, and an accessible search-help dialog.

**Architecture:** Add a focused Python search module that owns a custom Whoosh analyzer and parser factory, then inject it into the existing `WorkspaceService` schema. Keep the bridge result contract unchanged. Add a standalone Vue help dialog and let `HomeView` own its visibility, focus restoration, and search-error state.

**Tech Stack:** Python 3.13, Whoosh 2.7.4, pytest, Vue 3 `<script setup>`, Vitest, Vite, existing pywebview bridge and desktop CSS.

**Design Spec:** `docs/superpowers/specs/2026-08-15-desktop-search-capabilities-design.md`

---

## File Map

- Create `desktop/src/flatnotes_desktop/search.py`: technical analyzer and configured query-parser factory.
- Create `desktop/tests/test_search.py`: analyzer token and parser-plugin unit tests.
- Modify `desktop/src/flatnotes_desktop/workspace.py`: schema fields, field boosts, and parser factory integration.
- Modify `desktop/tests/test_workspace.py`: end-to-end query behavior, phrase safety, and ranking tests.
- Create `desktop/client/src/components/SearchHelpDialog.vue`: accessible syntax-help modal.
- Create `desktop/client/src/components/SearchHelpDialog.test.js`: source-contract tests matching existing frontend conventions.
- Modify `desktop/client/src/views/HomeView.vue`: help trigger, dialog state, focus restoration, and search-error handling.
- Modify `desktop/client/src/views/HomeView.test.js`: Home search/help integration-contract tests.
- Modify `desktop/client/src/style.css`: stable search controls, tooltip, dialog, error, and light-theme styling.
- Modify `desktop/client/src/style.test.js`: search-help style contract tests.

### Task 1: Add The Technical Analyzer And Query Parser

**Files:**

- Create: `desktop/tests/test_search.py`
- Create: `desktop/src/flatnotes_desktop/search.py`

- [ ] **Step 1: Write failing analyzer and parser tests**

Create `desktop/tests/test_search.py`:

```python
from whoosh.fields import Schema, TEXT
from whoosh.query import FuzzyTerm, Phrase, Prefix, Wildcard

from flatnotes_desktop.search import TECHNICAL_ANALYZER, build_query_parser


def analyzed_terms(value: str, mode: str) -> list[str]:
    return [token.text for token in TECHNICAL_ANALYZER(value, mode=mode)]


def parser_schema() -> Schema:
    return Schema(
        title=TEXT(analyzer=TECHNICAL_ANALYZER),
        content=TEXT(analyzer=TECHNICAL_ANALYZER),
        tags=TEXT(analyzer=TECHNICAL_ANALYZER),
    )


def test_index_analyzer_preserves_technical_terms_and_adds_parts():
    assert analyzed_terms("update_acct_config", "index") == [
        "update_acct_config",
        "update",
        "acct",
        "config",
    ]
    assert analyzed_terms("cwLUNC-tax_zones", "index") == [
        "cwlunc-tax_zones",
        "cw",
        "lunc",
        "tax",
        "zones",
    ]
    assert analyzed_terms("--node", "index") == ["--node", "node"]


def test_index_analyzer_preserves_addresses_hashes_and_urls():
    assert analyzed_terms("terra1abc234def", "index")[0] == "terra1abc234def"
    assert analyzed_terms("A1B2C3D4", "index")[0] == "a1b2c3d4"
    assert analyzed_terms("https://lcd.terra.dev:1317/cosmos", "index")[0] == (
        "https://lcd.terra.dev:1317/cosmos"
    )


def test_analyzer_keeps_plain_prose_clean_and_folds_accents():
    assert analyzed_terms("plain words", "index") == ["plain", "words"]
    assert analyzed_terms("café", "index") == ["cafe"]
    assert analyzed_terms("café", "query") == ["cafe"]


def test_query_analyzer_splits_without_duplicate_original_terms():
    assert analyzed_terms("update_acct_config", "query") == [
        "update",
        "acct",
        "config",
    ]


def test_parser_enables_fuzzy_prefix_wildcard_phrase_and_field_queries():
    parser = build_query_parser(parser_schema())

    assert {type(leaf) for leaf in parser.parse("terrd~").leaves()} == {FuzzyTerm}
    assert {type(leaf) for leaf in parser.parse("terra*").leaves()} == {Prefix}
    assert {type(leaf) for leaf in parser.parse("te?t").leaves()} == {Wildcard}
    assert {type(leaf) for leaf in parser.parse('"bonding curve"').leaves()} == {
        Phrase
    }
    assert {leaf.fieldname for leaf in parser.parse("title:curve").leaves()} == {
        "title"
    }
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run from repository root:

```bash
desktop/.venv/bin/pytest desktop/tests/test_search.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'flatnotes_desktop.search'`.

- [ ] **Step 3: Implement the analyzer and parser factory**

Create `desktop/src/flatnotes_desktop/search.py`:

```python
from collections.abc import Iterable, Iterator

from whoosh.analysis import (
    Analyzer,
    CharsetFilter,
    IntraWordFilter,
    LowercaseFilter,
    RegexTokenizer,
    Token,
)
from whoosh.fields import Schema
from whoosh.qparser import FuzzyTermPlugin, MultifieldParser, QueryParser
from whoosh.support.charset import accent_map


INTRAWORD_DELIMITERS = "-_'\"()!@#$%^&[]{}<>\\|;:,./`~=+"
TECHNICAL_MARKERS = frozenset("_-/:")


def _is_technical_term(text: str) -> bool:
    return any(marker in text for marker in TECHNICAL_MARKERS) or (
        any(character.isalpha() for character in text)
        and any(character.isdigit() for character in text)
    )


class TechnicalAnalyzer(Analyzer):
    """Index full technical tokens while querying their searchable parts."""

    def __init__(self):
        self.tokenizer = RegexTokenizer(r"\S+")
        # Keep wildcard characters intact while parsing wildcard queries.
        self.intraword = IntraWordFilter(delims=INTRAWORD_DELIMITERS)
        self.lowercase = LowercaseFilter()
        self.charset = CharsetFilter(accent_map)

    def __call__(self, value: str, **kwargs) -> Iterator[Token]:
        tokens = self.tokenizer(value, **kwargs)
        tokens = self._split(
            tokens,
            preserve_original=kwargs.get("mode") == "index",
        )
        tokens = self.lowercase(tokens)
        return self.charset(tokens)

    def _split(
        self,
        tokens: Iterable[Token],
        preserve_original: bool,
    ) -> Iterator[Token]:
        next_position = None
        for token in tokens:
            original = token.copy()
            if token.positions:
                if next_position is None:
                    next_position = token.pos
                token.pos = next_position
                original.pos = next_position

            parts = [part.copy() for part in self.intraword(iter([token]))]
            if preserve_original and _is_technical_term(original.text):
                yield original
            yield from parts

            if token.positions and parts:
                next_position = parts[-1].pos + 1


TECHNICAL_ANALYZER = TechnicalAnalyzer()


def build_query_parser(schema: Schema) -> QueryParser:
    parser = MultifieldParser(["title", "content", "tags"], schema)
    parser.add_plugin(FuzzyTermPlugin())
    return parser
```

Important: `INTRAWORD_DELIMITERS` intentionally omits `*` and `?`. Including them makes `te?t` parse as ordinary split terms instead of a Whoosh `Wildcard` query.

- [ ] **Step 4: Run analyzer/parser tests**

Run:

```bash
desktop/.venv/bin/pytest desktop/tests/test_search.py -q
```

Expected: `5 passed`.

- [ ] **Step 5: Commit the search configuration unit**

```bash
git add desktop/src/flatnotes_desktop/search.py desktop/tests/test_search.py
git commit -m "feat: add technical desktop search analyzer"
```

### Task 2: Apply The Analyzer, Fuzzy Parser, And Ranking To Workspace Search

**Files:**

- Modify: `desktop/tests/test_workspace.py`
- Modify: `desktop/src/flatnotes_desktop/workspace.py:5-7`
- Modify: `desktop/src/flatnotes_desktop/workspace.py:23-31`
- Modify: `desktop/src/flatnotes_desktop/workspace.py:55-60`

- [ ] **Step 1: Add failing workspace integration tests**

Append these tests to `desktop/tests/test_workspace.py`:

```python
def test_search_matches_technical_identifier_parts_and_full_values(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "technical.md").write_text(
        "update_acct_config cwLUNC-tax_zones terra1abc234def A1B2C3D4 --node",
        encoding="utf-8",
    )
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    for query in ["acct", "tax", "terra1abc234def", "A1B2C3D4", "node"]:
        assert [item.title for item in service.search(query)] == ["technical"]


def test_search_supports_accent_prefix_wildcard_fuzzy_and_phrase_queries(
    tmp_path: Path,
):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "guide.md").write_text(
        "Run terrad from the café during the bonding curve migration #chain",
        encoding="utf-8",
    )
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    assert [item.title for item in service.search("cafe")] == ["guide"]
    assert [item.title for item in service.search("terra*")] == ["guide"]
    assert [item.title for item in service.search("te?rad")] == ["guide"]
    assert [item.title for item in service.search("terrd~")] == ["guide"]
    assert [item.title for item in service.search('"bonding curve"')] == [
        "guide"
    ]
    assert [item.title for item in service.search("tags:chain")] == ["guide"]
    assert service.search("terr") == []


def test_title_and_tag_matches_rank_above_content_only_matches(tmp_path: Path):
    from flatnotes_desktop.workspace import WorkspaceService

    root = tmp_path / "notes"
    root.mkdir()
    (root / "needle.md").write_text("other text", encoding="utf-8")
    (root / "tag.md").write_text("#needle", encoding="utf-8")
    (root / "content.md").write_text("needle", encoding="utf-8")
    service = WorkspaceService(root, tmp_path / "index")
    service.rebuild()

    assert [item.title for item in service.search("needle")] == [
        "tag",
        "needle",
        "content",
    ]
    assert [item.title for item in service.search("title:needle")] == [
        "needle"
    ]
```

The quoted-phrase assertion is also the regression test for the current `KEYWORD` tag-position failure.

- [ ] **Step 2: Run workspace tests and verify the new cases fail**

Run:

```bash
desktop/.venv/bin/pytest desktop/tests/test_workspace.py -q
```

Expected: new cases fail because underscores are unsplit, accents are not folded, fuzzy syntax is not enabled, phrase search raises a tag-position `QueryError`, and boosts are absent.

- [ ] **Step 3: Wire the schema and parser into WorkspaceService**

Update imports and the schema/search sections of `desktop/src/flatnotes_desktop/workspace.py` so the complete top through `search()` reads:

```python
import shutil
from dataclasses import dataclass
from pathlib import Path

from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in, open_dir

from .paths import workspace_note_path
from .search import TECHNICAL_ANALYZER, build_query_parser


@dataclass(frozen=True)
class SearchResult:
    title: str
    path: Path


class WorkspaceService:
    """Recursive Markdown workspace backed by portable Whoosh index."""

    _serializable = False

    def __init__(self, root: Path, index_directory: Path):
        self.root = root.resolve()
        self.index_directory = index_directory
        self.schema = Schema(
            title=TEXT(
                stored=True,
                analyzer=TECHNICAL_ANALYZER,
                field_boost=2.0,
            ),
            path=ID(stored=True, unique=True),
            content=TEXT(analyzer=TECHNICAL_ANALYZER),
            tags=TEXT(analyzer=TECHNICAL_ANALYZER, field_boost=2.0),
        )

    def rebuild(self) -> None:
        self.index_directory.mkdir(parents=True, exist_ok=True)
        index = create_in(self.index_directory, self.schema)
        writer = index.writer()
        for path in self.list_files():
            content = path.read_text(encoding="utf-8")
            writer.add_document(
                title=self.title_for(path),
                path=str(path),
                content=content,
                tags=" ".join(self._tags(content)),
            )
        writer.commit()

    def rebuild_index(self) -> None:
        """Delete the current Whoosh index and rebuild it from workspace files."""
        if self.index_directory.is_dir():
            shutil.rmtree(self.index_directory)
        elif self.index_directory.exists():
            self.index_directory.unlink()
        self.rebuild()

    def search(self, term: str) -> list[SearchResult]:
        index = open_dir(self.index_directory)
        parser = build_query_parser(index.schema)
        with index.searcher() as searcher:
            hits = searcher.search(parser.parse(term))
            return [SearchResult(hit["title"], Path(hit["path"])) for hit in hits]
```

Keep `create()`, `rename()`, `delete()`, `list_files()`, `title_for()`, and `_tags()` unchanged below this block.

- [ ] **Step 4: Run focused backend tests**

Run:

```bash
desktop/.venv/bin/pytest desktop/tests/test_search.py desktop/tests/test_workspace.py desktop/tests/test_bridge.py -q
```

Expected: all focused backend tests pass. The bridge tests prove the result payload remains `{title, path}` and indexing-state guards remain intact.

- [ ] **Step 5: Commit workspace search integration**

```bash
git add desktop/src/flatnotes_desktop/workspace.py desktop/tests/test_workspace.py
git commit -m "feat: improve desktop workspace search"
```

### Task 3: Build The Search Help Dialog

**Files:**

- Create: `desktop/client/src/components/SearchHelpDialog.test.js`
- Create: `desktop/client/src/components/SearchHelpDialog.vue`
- Modify: `desktop/client/src/style.css:231-241`

- [ ] **Step 1: Write the failing dialog contract tests**

Create `desktop/client/src/components/SearchHelpDialog.test.js`:

```js
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const component = readFileSync(
  fileURLToPath(new URL("./SearchHelpDialog.vue", import.meta.url)),
  "utf8",
);

describe("SearchHelpDialog", () => {
  it("exposes an accessible modal with every close path", () => {
    expect(component).toMatch(/id="search-help-dialog"/);
    expect(component).toMatch(/role="dialog"/);
    expect(component).toMatch(/aria-modal="true"/);
    expect(component).toMatch(/aria-labelledby="search-help-title"/);
    expect(component).toMatch(/@click\.self="close"/);
    expect(component).toMatch(/@keydown\.escape\.stop\.prevent="close"/);
    expect(component).toMatch(/aria-label="Close search help"/);
    expect(component).toMatch(/closeButton\.value\?\.focus\(\)/);
  });

  it("documents the supported query formats", () => {
    for (const example of [
      "terra validator",
      "&quot;bonding curve&quot;",
      "terra*",
      "te?t",
      "terrd~",
      "terrad~2",
      "title:curve",
      "tags:terra",
      "terra AND validator",
    ]) {
      expect(component).toContain(example);
    }
  });
});
```

- [ ] **Step 2: Run the focused frontend test and verify it fails**

Run from `desktop/client`:

```bash
npm test -- src/components/SearchHelpDialog.test.js
```

Expected: test fails because `SearchHelpDialog.vue` does not exist.

- [ ] **Step 3: Implement the help dialog**

Create `desktop/client/src/components/SearchHelpDialog.vue`:

```vue
<template>
  <div class="modal-backdrop" role="presentation" @click.self="close">
    <section
      id="search-help-dialog"
      class="search-help-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="search-help-title"
      @keydown.escape.stop.prevent="close"
    >
      <header>
        <h2 id="search-help-title">Search help</h2>
        <button
          ref="closeButton"
          class="search-help-close"
          type="button"
          aria-label="Close search help"
          @click="close"
        >
          &times;
        </button>
      </header>
      <table>
        <thead>
          <tr><th>Format</th><th>Example</th></tr>
        </thead>
        <tbody>
          <tr><td>All words</td><td><code>terra validator</code></td></tr>
          <tr><td>Exact phrase</td><td><code>&quot;bonding curve&quot;</code></td></tr>
          <tr><td>Prefix</td><td><code>terra*</code></td></tr>
          <tr><td>One wildcard</td><td><code>te?t</code></td></tr>
          <tr><td>Fuzzy, one edit</td><td><code>terrd~</code></td></tr>
          <tr><td>Fuzzy, two edits</td><td><code>terrad~2</code></td></tr>
          <tr><td>Title field</td><td><code>title:curve</code></td></tr>
          <tr><td>Content field</td><td><code>content:node</code></td></tr>
          <tr><td>Tag field</td><td><code>tags:terra</code></td></tr>
          <tr><td>Boolean</td><td><code>terra AND validator</code></td></tr>
        </tbody>
      </table>
      <p class="search-help-note">
        Prefix searches perform best without a leading wildcard. Fuzzy distances
        above two can be slow.
      </p>
    </section>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

const emit = defineEmits(["close"]);
const closeButton = ref();

function close() { emit("close"); }

onMounted(() => nextTick(() => closeButton.value?.focus()));
</script>
```

- [ ] **Step 4: Add dialog styling**

Append this block beside existing modal styles in `desktop/client/src/style.css`:

```css
.search-help-dialog { width: min(620px, calc(100vw - 40px)); max-height: calc(100vh - 40px); overflow: auto; padding: 20px; border: 1px solid #78716c; border-radius: 8px; background: #292524; color: #f5f5f4; box-shadow: 0 8px 30px #0008; }
.search-help-dialog header { display: flex; gap: 16px; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.search-help-dialog h2 { margin: 0; font-size: 20px; }
.search-help-close { width: 32px; height: 32px; padding: 0; font-size: 22px; line-height: 1; }
.search-help-dialog table { width: 100%; border-collapse: collapse; font-size: 13px; }
.search-help-dialog th, .search-help-dialog td { padding: 8px 10px; border-bottom: 1px solid #44403c; text-align: left; vertical-align: top; }
.search-help-dialog th { color: #d6d3d1; font-weight: 600; }
.search-help-dialog code { color: #fdba74; white-space: nowrap; }
.home .search-help-note { margin: 14px 0 0; color: #a8a29e; font-size: 12px; }
:root[data-theme="light"] .search-help-dialog { border-color: #a8a29e; background: #ffffff; color: #292524; box-shadow: 0 8px 30px #57534e55; }
:root[data-theme="light"] .search-help-dialog th, :root[data-theme="light"] .search-help-dialog td { border-color: #e7e5e4; }
:root[data-theme="light"] .search-help-dialog th { color: #44403c; }
:root[data-theme="light"] .search-help-dialog code { color: #c2410c; }
:root[data-theme="light"] .home .search-help-note { color: #57534e; }
```

- [ ] **Step 5: Run the dialog test and frontend build**

Run from `desktop/client`:

```bash
npm test -- src/components/SearchHelpDialog.test.js
npm run build
```

Expected: focused test passes and Vite production build completes.

- [ ] **Step 6: Commit the standalone help dialog**

```bash
git add desktop/client/src/components/SearchHelpDialog.vue desktop/client/src/components/SearchHelpDialog.test.js desktop/client/src/style.css
git commit -m "feat: add desktop search help dialog"
```

### Task 4: Integrate Help And Search Errors Into HomeView

**Files:**

- Modify: `desktop/client/src/views/HomeView.test.js`
- Modify: `desktop/client/src/views/HomeView.vue`
- Modify: `desktop/client/src/style.css:76-100`
- Modify: `desktop/client/src/style.test.js`

- [ ] **Step 1: Replace HomeView tests with the expanded failing contract**

Replace `desktop/client/src/views/HomeView.test.js` with:

```js
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  fileURLToPath(new URL("./HomeView.vue", import.meta.url)),
  "utf8",
);

describe("HomeView search", () => {
  it("blocks submission while the index is busy", () => {
    expect(source).toMatch(/props\.indexBusy\s*\|\|\s*!query/);
  });

  it("opens accessible search help and restores trigger focus", () => {
    expect(source).toMatch(/SearchHelpDialog/);
    expect(source).toMatch(/aria-label="Search help"/);
    expect(source).toMatch(/:aria-expanded="searchHelpOpen"/);
    expect(source).toMatch(/aria-controls="search-help-dialog"/);
    expect(source).toMatch(/data-tooltip="Search help"/);
    expect(source).toMatch(/@close="closeSearchHelp"/);
    expect(source).toMatch(/searchHelpButton\.value\?\.focus\(\)/);
  });

  it("catches search failures and exposes an alert", () => {
    expect(source).toMatch(/try\s*\{/);
    expect(source).toMatch(/catch\s*\(error\)/);
    expect(source).toMatch(/results\.value\s*=\s*\[\]/);
    expect(source).toMatch(/role="alert"/);
  });
});
```

- [ ] **Step 2: Add failing search-help style tests**

Add this test to `desktop/client/src/style.test.js`:

```js
it("keeps search help controls stable and themed", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/\.search-help-button\s*\{[^}]*width:\s*40px[^}]*border-radius:\s*0/);
  expect(css).toMatch(/\.search-help-button::after\s*\{[^}]*content:\s*attr\(data-tooltip\)/);
  expect(css).toMatch(/\.search-help-button:hover::after,[\s\S]*\.search-help-button:focus-visible::after/);
  expect(css).toMatch(/\.home\s+\.search-error\s*\{[^}]*color:\s*#f87171/);
  expect(css).toMatch(/:root\[data-theme="light"\]\s+\.search-help-dialog\s*\{[^}]*background:\s*#ffffff[^}]*color:\s*#292524/);
});
```

- [ ] **Step 3: Run focused Home/style tests and verify failure**

Run from `desktop/client`:

```bash
npm test -- src/views/HomeView.test.js src/style.test.js
```

Expected: new assertions fail because HomeView has no help state, focus logic, or search-error UI and the search trigger styles do not exist.

- [ ] **Step 4: Replace HomeView with the integrated implementation**

Replace `desktop/client/src/views/HomeView.vue` with:

```vue
<template>
  <main class="home">
    <h1>simpleMD</h1>
    <p v-if="workspace">Workspace: {{ workspace }}</p>
    <p v-else>No workspace selected.</p>
    <button type="button" @click="$emit('select-workspace')">Select workspace</button>
    <button class="rebuild-index-button" type="button" :disabled="!workspace || indexBusy" @click="$emit('rebuild-index')">
      {{ indexBusy ? "Rebuilding…" : "Rebuild Index" }}
    </button>
    <button type="button" @click="$emit('open-markdown')">Open Markdown</button>
    <p v-if="indexMessage" class="index-status" :class="{ error: indexError }" role="status" aria-live="polite">{{ indexMessage }}</p>
    <form @submit.prevent="submitSearch">
      <input v-model="term" aria-label="Search notes" :disabled="indexBusy" placeholder="Search notes" />
      <button
        ref="searchHelpButton"
        class="search-help-button"
        type="button"
        aria-label="Search help"
        :aria-expanded="searchHelpOpen"
        aria-controls="search-help-dialog"
        data-tooltip="Search help"
        @click="searchHelpOpen = true"
      >
        ?
      </button>
      <button type="submit" :disabled="indexBusy">Search</button>
    </form>
    <p v-if="searchError" class="search-error" role="alert">{{ searchError }}</p>
    <ul>
      <li v-for="result in results" :key="result.path"><button type="button" @click="$emit('open-result', result)">{{ result.title }}</button></li>
    </ul>
    <SearchHelpDialog v-if="searchHelpOpen" @close="closeSearchHelp" />
  </main>
</template>

<script setup>
import { nextTick, ref, watch } from "vue";
import { searchWorkspace } from "../api/desktop.js";
import SearchHelpDialog from "../components/SearchHelpDialog.vue";

const props = defineProps({
  workspace: { type: String, default: null },
  indexBusy: { type: Boolean, default: false },
  indexMessage: { type: String, default: "" },
  indexError: { type: Boolean, default: false },
});
defineEmits(["select-workspace", "rebuild-index", "open-markdown", "open-result"]);
const term = ref("");
const results = ref([]);
const searchError = ref("");
const searchHelpOpen = ref(false);
const searchHelpButton = ref();

watch(() => props.workspace, () => {
  term.value = "";
  results.value = [];
  searchError.value = "";
  searchHelpOpen.value = false;
});

async function submitSearch() {
  const query = term.value.trim();
  if (props.indexBusy || !query) return;
  searchError.value = "";
  try {
    results.value = await searchWorkspace(query);
  } catch (error) {
    results.value = [];
    searchError.value = `Search failed: ${error?.message || "Unknown error."}`;
  }
}

async function closeSearchHelp() {
  searchHelpOpen.value = false;
  await nextTick();
  searchHelpButton.value?.focus();
}
</script>
```

- [ ] **Step 5: Update search-control, tooltip, and error CSS**

Replace the existing `.home form`, `.home input`, and `.home form button` rules in `desktop/client/src/style.css` with:

```css
.home form { display: flex; width: min(620px, 100%); margin-top: 16px; }
.home input { flex: 1; min-width: 0; border: 1px solid #44403c; border-radius: 6px 0 0 6px; background: #1c1917; color: #f5f5f4; padding: 9px 12px; outline: 0; }
.home input:focus { border-color: #a8a29e; }
.home .search-help-button { position: relative; flex: 0 0 40px; width: 40px; border-left: 0; border-radius: 0; padding: 0; font-weight: 700; }
.home form > button[type="submit"] { border-radius: 0 6px 6px 0; }
.search-help-button::after { position: absolute; left: 50%; bottom: calc(100% + 8px); z-index: 10; padding: 5px 7px; border-radius: 4px; background: #0c0a09; color: #fafaf9; content: attr(data-tooltip); font-size: 11px; font-weight: 400; line-height: 1; opacity: 0; pointer-events: none; transform: translateX(-50%); white-space: nowrap; }
.search-help-button:hover::after, .search-help-button:focus-visible::after { opacity: 1; }
.home .search-error { width: min(620px, 100%); margin: 8px 0 0; color: #f87171; }
```

Add this light-theme override beside the existing home status rules:

```css
:root[data-theme="light"] .home .search-error { color: #b91c1c; }
```

- [ ] **Step 6: Run focused and full frontend verification**

Run from `desktop/client`:

```bash
npm test -- src/components/SearchHelpDialog.test.js src/views/HomeView.test.js src/style.test.js
npm test
npm run build
```

Expected: all Vitest tests pass and Vite emits a successful production build.

- [ ] **Step 7: Commit HomeView integration**

```bash
git add desktop/client/src/views/HomeView.vue desktop/client/src/views/HomeView.test.js desktop/client/src/style.css desktop/client/src/style.test.js
git commit -m "feat: expose desktop search syntax help"
```

### Task 5: Run Full Verification And Manual Acceptance

**Files:**

- Verify only; no planned source changes.

- [ ] **Step 1: Run the complete Python desktop suite**

Run from repository root:

```bash
desktop/.venv/bin/pytest desktop/tests -q
```

Expected: all desktop Python tests pass.

- [ ] **Step 2: Run the complete frontend suite and build**

Run:

```bash
cd desktop/client
npm test
npm run build
```

Expected: all Vitest tests pass; Vite production build succeeds without warnings introduced by this feature.

- [ ] **Step 3: Inspect the final change set**

Run from repository root:

```bash
git status --short
git diff --check HEAD~4..HEAD
git log -4 --oneline
```

Expected: only the planned backend/frontend search files are part of the four feature commits; `git diff --check` prints nothing. Preserve any unrelated pre-existing worktree changes.

- [ ] **Step 4: Run desktop manual acceptance**

On Windows, build and launch the packaged desktop app:

```powershell
cd desktop
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build_windows.ps1
.\dist\simpleMD.exe
```

Select a small test workspace and verify:

- Search stays disabled while the background index rebuild runs.
- `acct` finds content containing `update_acct_config`.
- `tax` finds content containing `cwLUNC-tax_zones`.
- Exact address and hash queries find their note.
- `cafe` finds `café`.
- `terra*`, `te?rad`, `terrd~`, `"bonding curve"`, `title:curve`, and `tags:chain` behave as documented.
- Plain `terr` does not silently become a substring, prefix, or fuzzy query.
- Title and tag matches appear above content-only matches for an equivalent term.
- Help tooltip appears on hover and keyboard focus.
- Help dialog opens by click/keyboard and closes by close button, Escape, and backdrop.
- Focus returns to the help button after the dialog closes.
- Dialog and alert styling remain readable in dark and light themes.

If verification exposes a defect, add a failing regression test first, make the smallest correction, rerun the affected focused tests plus both full suites, and commit that correction separately.
