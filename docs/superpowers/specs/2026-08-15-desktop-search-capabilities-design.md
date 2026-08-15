# Desktop Search Capabilities Design

## Summary

Improve simpleMD desktop workspace search without turning every query into an automatic substring search. Search will remain predictable and Whoosh-backed while gaining code-aware tokenization, accent folding, explicit fuzzy matching, stronger relevance ranking, and in-app syntax help.

This design applies only to the desktop application under `desktop/`. The server-backed web application keeps its existing search implementation.

## Goals

- Let blockchain and command identifiers match by useful components. For example, `update_acct_config` must match `update`, `acct`, and `config`.
- Preserve searchable full technical values such as addresses, transaction hashes, command flags, URLs, and compound identifiers.
- Let an unaccented query match accented indexed text, such as `cafe` matching `café`.
- Enable explicit fuzzy terms using Whoosh syntax such as `terrd~` and `terrad~2`.
- Keep explicit prefix and wildcard syntax such as `terra*` and `te?t`.
- Rank title and tag matches above content-only matches.
- Keep quoted phrases and field-restricted searches functional.
- Provide discoverable search syntax through a tooltip-triggered help dialog.
- Apply the new schema through the desktop application's existing background index rebuild lifecycle.

## Non-Goals

- Automatic prefix, fuzzy, or substring expansion for plain terms.
- N-gram indexing or leading-wildcard optimization.
- Stemming or lemmatization in this phase.
- Search-result highlighting, pagination, or snippets.
- Changes to the server-backed web search.
- A replacement search engine or Whoosh upgrade.

## Current State

`WorkspaceService` defines the desktop Whoosh schema, rebuilds the index, parses queries with `MultifieldParser`, and returns title/path results. `DesktopBridge.search_workspace()` serializes those results. `HomeView.vue` submits a query through the pywebview API and displays the returned titles.

Current `TEXT` fields use Whoosh's `StandardAnalyzer`. It lowercases and tokenizes prose, but it does not fold accents or stem words, and it retains underscores inside a token. Wildcards and phrases are already part of the default parser. Fuzzy syntax is absent because `FuzzyTermPlugin` is not installed.

Current tags use `KEYWORD`, which does not store positions. Because `MultifieldParser` sends an unfielded quoted phrase to title, content, and tags, a phrase query can raise `QueryError` when Whoosh tries to run the phrase against tags. The new schema must remove that failure.

## Architecture

### Search Configuration Module

Create `desktop/src/flatnotes_desktop/search.py` as the single owner of desktop search configuration. It will export:

- A technical identifier predicate/filter used only during indexing to retain full technical terms.
- A technical analyzer shared by title, content, and tags.
- A `build_query_parser(schema)` factory that configures `MultifieldParser` and `FuzzyTermPlugin`.

`workspace.py` will continue to own workspace IO, index writes, and result mapping. It will import the analyzer and parser factory instead of embedding search configuration. The bridge API and result payload remain unchanged.

### Technical Analyzer

The analyzer pipeline will use Whoosh components in this order:

1. Tokenize non-whitespace sequences so punctuation remains available to technical-token analysis.
2. During indexing, retain the original token only when it looks technical: it contains `_`, `-`, `/`, `:`, or both letters and digits.
3. Also pass every token through `IntraWordFilter` to produce subterms from underscores, hyphens, case changes, and letter/number transitions.
4. Lowercase all emitted terms.
5. Apply `CharsetFilter(accent_map)` for accent folding.

During query analysis, use the split-term path without adding a duplicate full token. This keeps ordinary phrase analysis clean while allowing indexed technical originals and their parts to coexist.

Required analyzer examples:

| Input | Required searchable terms |
| --- | --- |
| `update_acct_config` | full normalized identifier, `update`, `acct`, `config` |
| `cwLUNC-tax_zones` | full normalized identifier, `cw`, `lunc`, `tax`, `zones` |
| `terra1abc234def` | full normalized address plus analyzer subterms |
| `A1B2C3D4` | full normalized hash plus analyzer subterms |
| `--node` | full normalized flag and `node` |
| `café` | unaccented `cafe` term |

Exact term sets and positions must be locked down by unit tests before wiring the analyzer into the schema. Ordinary prose must emit one token per word, without duplicate postings.

### Schema And Ranking

Use the technical analyzer for all three searchable fields:

- `title`: stored `TEXT`, field boost `2.0`.
- `content`: non-stored `TEXT`, field boost `1.0`.
- `tags`: non-stored positional `TEXT`, field boost `2.0`.
- `path`: unchanged stored unique `ID`.

Changing tags from `KEYWORD` to positional `TEXT` prevents phrase queries from targeting a field without positions. Tag extraction remains in `WorkspaceService._tags()` and supplies a whitespace-separated string as it does now.

Boosts belong in the schema only. Do not also apply parser field boosts, which would multiply the weighting twice.

### Query Parsing

`build_query_parser(schema)` will search `title`, `content`, and `tags`. It will preserve Whoosh's default phrase, field, Boolean, prefix, and wildcard plugins, then add `FuzzyTermPlugin`.

Supported help syntax:

| Format | Example | Behavior |
| --- | --- | --- |
| Words | `terra validator` | Match all entered terms using Whoosh's default AND grouping. |
| Phrase | `"bonding curve"` | Match adjacent analyzed terms. |
| Prefix | `terra*` | Match indexed terms beginning with `terra`. |
| Single wildcard | `te?t` | Match one character at `?`. |
| Fuzzy | `terrd~` | Match terms within the default one-edit distance. |
| Fuzzy distance | `terrad~2` | Match terms within two edits; the help text will not recommend larger distances. |
| Field | `title:curve`, `content:node`, `tags:terra` | Restrict the next term or grouped expression to one field. |
| Boolean | `terra AND validator`, `terra OR luna`, `terra NOT classic` | Combine or exclude clauses. |

Leading wildcard examples such as `*terra` will not be promoted because Whoosh documents them as slow. Plain `terr` will not silently become `terr*`, `terr~`, or `*terr*`.

### Index Lifecycle

No new migration API is needed. Desktop startup and workspace selection already queue a background `WorkspaceService.rebuild()`, and search remains disabled while rebuilding. That rebuild creates an index with the new schema before queries are accepted. The existing manual Rebuild Index action remains the recovery path.

Regression tests must prove that rebuilds use the new analyzer and remove stale index state. No code should attempt to query a pre-change index while the background rebuild is active.

## Search Help UI

Add `desktop/client/src/components/SearchHelpDialog.vue`. `HomeView.vue` will own a Boolean open state and render the dialog beside its existing search workflow.

Place a compact `?` icon button next to the search input. The button will have:

- `type="button"` so it never submits the search form.
- `aria-label="Search help"`.
- `aria-expanded` and `aria-controls` tied to dialog state.
- A hover/focus tooltip reading `Search help`.

Clicking the button opens a themed modal using the existing `.modal-backdrop` visual pattern. The dialog will show the supported-format table above, concise performance guidance, and a clear close control. It must close through the close button, Escape, or backdrop click. Opening moves focus to the dialog close button; closing returns focus to the help button.

The dialog uses `role="dialog"`, `aria-modal="true"`, and an accessible heading reference. Dark and light styles belong in `desktop/client/src/style.css`, near existing dialog styles. The search form keeps stable dimensions when the icon appears.

## Error Handling

Backend result shape stays `[{title, path}]`. Parser and index exceptions continue to reject the pywebview call. `HomeView.vue` will catch search failures, clear stale results, and show a concise inline `role="alert"` message instead of leaving an unhandled promise rejection.

Opening or closing help never changes the query or current results. Changing workspace clears query, results, help state, and search error state.

## Testing

### Python

Create focused analyzer/parser tests in `desktop/tests/test_search.py`:

- Technical identifiers emit full normalized terms plus expected parts.
- Addresses, hashes, flags, and URLs retain a full normalized term.
- Ordinary prose emits no duplicate terms.
- Accent folding works in index and query modes.
- Parser output supports prefix, wildcard, phrase, field, Boolean, and fuzzy syntax.
- Fuzzy and prefix integration queries return expected notes.
- A plain partial term does not become an automatic substring query.

Extend `desktop/tests/test_workspace.py`:

- Component searches find underscore, hyphen, and mixed-case identifier parts.
- Exact address/hash queries return the containing note.
- `cafe` finds accented content.
- Quoted phrases complete without a tag-position error.
- Title and tag matches sort above an equivalent content-only match.
- Rebuilding applies the new schema and removes stale behavior.

Bridge tests need change only if search error behavior alters the bridge contract; this design does not require that change.

### Frontend

Create `desktop/client/src/components/SearchHelpDialog.test.js` following current component test conventions. Verify dialog roles, heading association, close paths, and documented syntax examples.

Extend `desktop/client/src/views/HomeView.test.js` to verify help-button semantics, dialog mounting, state reset, focus-return hooks, and search error rendering. Extend `desktop/client/src/style.test.js` for dark/light dialog surfaces, tooltip visibility rules, and stable search-control sizing.

### Verification

Run focused Python and frontend tests first, then full suites:

```bash
desktop/.venv/bin/pytest desktop/tests/test_search.py desktop/tests/test_workspace.py desktop/tests/test_bridge.py -q
desktop/.venv/bin/pytest desktop/tests -q
cd desktop/client && npm test
cd desktop/client && npm run build
```

Manual verification in the desktop app must cover search while indexing, each documented syntax example, result ordering, both themes, keyboard-only help interaction, and dialog focus restoration.

## Documentation References

- Whoosh analysis API: <https://whoosh.readthedocs.io/en/latest/api/analysis.html>
- Whoosh schema and field boosts: <https://whoosh.readthedocs.io/en/latest/schema.html>
- Whoosh query language: <https://whoosh.readthedocs.io/en/latest/querylang.html>
- Whoosh parser plugins and fuzzy terms: <https://whoosh.readthedocs.io/en/latest/parsing.html>
