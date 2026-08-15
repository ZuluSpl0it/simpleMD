# Desktop Search

This guide documents search in the simpleMD Windows desktop application. The
desktop search is a Whoosh full-text index over the selected Markdown workspace.
It is intentionally explicit: a normal term is not automatically expanded into
every substring, prefix, or spelling variant.

The short syntax table is also available from the `?` button beside the search
box. This file explains the implementation behind that help and gives examples
for diagnosing unexpected results.

## Quick Reference

| Query | Meaning |
| --- | --- |
| `terra` | Find the term `terra` in the title, content, or tags. |
| `terra validator` | Require both terms; each term may occur in a different field. |
| `"bonding curve"` | Match the analyzed terms as a phrase. |
| `terra*` | Prefix query; match indexed terms beginning with `terra`. |
| `te?t` | Wildcard query; `?` stands for one character. |
| `terrad~` | Fuzzy query using Whoosh's default edit distance of one. |
| `terrad~2` | Fuzzy query allowing up to two edits. |
| `title:curve` | Search only the title field. |
| `content:node` | Search only note content. |
| `tags:terra` | Search only extracted hashtags. |
| `terra AND validator` | Require both expressions. |
| `terra OR luna` | Match either expression. |
| `terra NOT classic` | Match `terra` while excluding `classic`. |

Queries are case-insensitive. Accents are folded, so `cafe` can match `café`.
Use parentheses when combining more complicated Boolean expressions, for
example `(terra OR luna) AND validator`.

## What Plain Search Does

The parser searches three fields for an unqualified term:

- `title`: the workspace-relative Markdown filename, without `.md`.
- `content`: the complete Markdown file text.
- `tags`: hashtags extracted from content, without the leading `#`.

Multiple unquoted words are combined with an AND relationship. Each individual
word is expanded across the three fields, so `terra validator` can match a note
where `terra` is in the title and `validator` is in the body. A field prefix such
as `title:` changes that behavior for the following expression.

Plain `terr` does **not** match `terrad` unless the indexed text contains the
term `terr`. Use `terr*` for a prefix or `terrd~` for a spelling-neighbor query.
Automatic substring matching is deliberately not enabled because it produces
noisy results and makes short queries expensive.

## Technical Identifiers

Desktop notes often contain commands, flags, addresses, hashes, and contract
identifiers rather than ordinary prose. The custom analyzer in
[`desktop/src/flatnotes_desktop/search.py`](desktop/src/flatnotes_desktop/search.py)
handles both use cases.

During indexing, a technical token is stored in two forms:

1. The normalized full token, when it contains technical punctuation or a mix
   of letters and digits.
2. The searchable parts produced by Whoosh's `IntraWordFilter`.

Examples:

| Source text | Searchable examples |
| --- | --- |
| `update_acct_config` | `update_acct_config`, `update`, `acct`, `config` |
| `cwLUNC-tax_zones` | `cwlunc-tax_zones`, `cw`, `lunc`, `tax`, `zones` |
| `--node` | `--node`, `node` |
| `terra1abc234def` | the full address plus analyzer-derived parts |
| `A1B2C3D4` | `a1b2c3d4` plus analyzer-derived parts |
| `https://lcd.terra.dev:1317/cosmos` | the full URL plus analyzer-derived parts |

This means `acct`, `tax`, `node`, or an exact address can find a note without
discarding the original technical value. Query analysis emits the parts without
duplicating the full technical token, keeping ordinary phrases clean.

The analyzer also lowercases terms and applies Whoosh's accent map. It does not
stem prose: `migrate`, `migrated`, and `migration` remain separate terms. That
is intentional because stemming technical commands and identifiers can create
incorrect matches.

## Relevance And Fields

The schema is defined in
[`desktop/src/flatnotes_desktop/workspace.py`](desktop/src/flatnotes_desktop/workspace.py):

| Field | Stored? | Boost |
| --- | --- | --- |
| `title` | Yes | `2.0` |
| `content` | No | `1.0` |
| `tags` | No | `2.0` |
| `path` | Yes, unique ID | Not searched as full text |

Title and tag matches therefore rank above an otherwise equivalent content-only
match. The search API returns only the note title and path; snippets and result
highlighting are not currently generated.

## How Whoosh Is Used

[Whoosh](https://whoosh.readthedocs.io/en/latest/) is a pure-Python indexing and
search library. simpleMD uses these Whoosh concepts:

- **Schema**: declares fields, analyzers, storage, and field boosts.
- **TEXT**: analyzed full-text fields used for title, content, and tags.
- **ID**: an untokenized stored field used for the unique note path.
- **Analyzer**: converts source text into normalized indexed/query terms.
- **Query parser**: converts user syntax into Whoosh query objects.
- **Index writer**: writes one document per Markdown file during a rebuild.
- **Searcher**: executes the parsed query and returns ranked hits.

`build_query_parser()` creates a `MultifieldParser` for `title`, `content`, and
`tags`, then installs `FuzzyTermPlugin`. Whoosh's normal parser plugins provide
phrases, field restrictions, Boolean operators, prefixes, and wildcards. The
`~` suffix is therefore explicit fuzzy syntax, not an automatic behavior of
every query.

Useful upstream references:

- [Schema and fields](https://whoosh.readthedocs.io/en/latest/schema.html)
- [Analysis API](https://whoosh.readthedocs.io/en/latest/api/analysis.html)
- [Stemming](https://whoosh.readthedocs.io/en/latest/stemming.html)
- [Query language](https://whoosh.readthedocs.io/en/latest/querylang.html)
- [Parser plugins](https://whoosh.readthedocs.io/en/latest/parsing.html)
- [Query API](https://whoosh.readthedocs.io/en/latest/api/query.html)

## Index Lifecycle

The index is derived data; Markdown files remain the source of truth. When a
workspace is selected or restored, the desktop bridge queues a background
rebuild. Search is held while `_indexing` is true, so a query cannot run against
an index built with an older workspace or schema.

The **Rebuild Index** action removes the current index directory and writes a
fresh one. Creating, renaming, deleting, or saving a note also schedules a
rebuild. A rebuild is required after changing analyzers or field definitions;
old postings cannot be retroactively re-analyzed.

## Performance Guidance

- Prefer `terra*` to a leading wildcard such as `*terra`.
- Keep fuzzy distance at one or two (`term~` or `term~2`). Larger distances can
  become slow because Whoosh must compare more candidate terms.
- Use field restrictions (`title:`, `tags:`) when the workspace is large.
- Quote only the phrase you need; quoted text is analyzed, not a raw byte match.
- Avoid very short fuzzy or wildcard queries, which naturally produce many hits.

## Troubleshooting

**A partial word returns nothing.** Use a prefix (`terra*`) or fuzzy query
(`terrad~`) instead of expecting substring matching.

**A new note is missing.** Wait for indexing to finish. If files were changed by
another program, use **Rebuild Index**.

**An identifier only matches part of the expected text.** Search the full value
first. Technical tokens are preserved, but punctuation and case are normalized
for lookup; an exact query must use the normalized searchable value.

**A query fails after a schema change.** Rebuild the index. An index created with
an older schema is not compatible with the new analyzer or field layout.

**A result is lower than expected.** Check whether the match is in content
instead of title or tags. The schema intentionally boosts title and tags, while
the bridge returns Whoosh's ranked order unchanged.

## Implementation Map

- Analyzer and parser: [`desktop/src/flatnotes_desktop/search.py`](desktop/src/flatnotes_desktop/search.py)
- Schema, rebuild, and search execution: [`desktop/src/flatnotes_desktop/workspace.py`](desktop/src/flatnotes_desktop/workspace.py)
- Bridge/indexing state: [`desktop/src/flatnotes_desktop/bridge.py`](desktop/src/flatnotes_desktop/bridge.py)
- Search input and help dialog: [`desktop/client/src/views/HomeView.vue`](desktop/client/src/views/HomeView.vue) and [`desktop/client/src/components/SearchHelpDialog.vue`](desktop/client/src/components/SearchHelpDialog.vue)
- Analyzer/parser tests: [`desktop/tests/test_search.py`](desktop/tests/test_search.py)
