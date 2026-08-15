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
