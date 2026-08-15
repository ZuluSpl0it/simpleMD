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
