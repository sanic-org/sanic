from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import ClassVar

from msgspec import Struct
from webapp.display.page import Page


class Stemmer:
    STOP_WORDS: ClassVar[set[str]] = set(
        "a about above after again against all am an and any are aren't as at be because been before being below between both but by can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor not of off on once only or other ought our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves".split()  # noqa: E501
    )
    PREFIXES = set("auto be fore over re un under".split())
    SUFFIXES = set(
        "able al ance ant ate ed en er ful hood ing ion ish ity ive ize less ly ment ness ous ship sion tion y".split()  # noqa: E501
    )
    VOWELS = set("aeiou")
    PLURALIZATION = set("s es ies".split())

    def stem(self, word: str) -> str:
        if word in self.STOP_WORDS:
            return word
        if word in self.PREFIXES:
            return word
        for suffix in self.SUFFIXES | self.PLURALIZATION:
            if word.endswith(suffix):
                return self._stem(word[: -len(suffix)])
        return word

    def _stem(self, word: str) -> str:
        if word.endswith("e"):
            return word[:-1]
        if word.endswith("y") and word[-2] not in self.VOWELS:
            return word[:-1]
        return word

    def __call__(self, word: str) -> str:
        return self.stem(word)


class Document(Struct, kw_only=True):
    TITLE_WEIGHT: ClassVar[int] = 3
    BODY_WEIGHT: ClassVar[int] = 1

    page: Page
    language: str
    term_frequency: dict[str, float] = {}

    @property
    def title(self) -> str:
        return self.page.meta.title

    @property
    def text(self) -> str:
        return self.page.content

    @property
    def weighted_text(self) -> str:
        """Return the text with the title repeated."""
        return " ".join(
            [self.title] * self.TITLE_WEIGHT + [self.text] * self.BODY_WEIGHT
        )

    def _term_frequency(self, stemmer: Stemmer) -> None:
        """Count the number of times each word appears in the document."""
        words = [
            stemmer(word)
            for word in self.weighted_text.lower().split()
            if word not in Stemmer.STOP_WORDS
        ]
        num_words = len(words)
        word_count = Counter(words)
        self.term_frequency = {
            word: count / num_words for word, count in word_count.items()
        }

    def process(self, stemmer: Stemmer) -> Document:
        """Process the document."""
        self._term_frequency(stemmer)
        return self


def _inverse_document_frequency(docs: list[Document]) -> dict[str, float]:
    """Count the number of documents each word appears in."""
    num_docs = len(docs)
    word_count: Counter[str] = Counter()
    for doc in docs:
        word_count.update(doc.term_frequency.keys())
    return {word: num_docs / count for word, count in word_count.items()}


def _tf_idf_vector(
    document: Document, idf: dict[str, float]
) -> dict[str, float]:
    """Calculate the TF-IDF vector for a document."""
    return {
        word: tf * idf[word]
        for word, tf in document.term_frequency.items()
        if word in idf
    }


def _cosine_similarity(
    vec1: dict[str, float], vec2: dict[str, float]
) -> float:
    """Calculate the cosine similarity between two vectors."""
    if not vec1 or not vec2:
        return 0.0
    dot_product = sum(vec1.get(word, 0) * vec2.get(word, 0) for word in vec1)
    magnitude1 = sum(value**2 for value in vec1.values()) ** 0.5
    magnitude2 = sum(value**2 for value in vec2.values()) ** 0.5
    return dot_product / (magnitude1 * magnitude2)


def _search(
    query: str,
    language: str,
    vectors: list[dict[str, float]],
    idf: dict[str, float],
    documents: list[Document],
    stemmer: Stemmer,
) -> list[tuple[float, Document]]:
    dummy_page = Page(Path(), query)
    tf_idf_query = _tf_idf_vector(
        Document(page=dummy_page, language=language).process(stemmer), idf
    )
    similarities = [
        _cosine_similarity(tf_idf_query, vector) for vector in vectors
    ]
    return [
        (similarity, document)
        for similarity, document in sorted(
            zip(similarities, documents),
            reverse=True,
            key=lambda pair: pair[0],
        )[:10]
        if similarity > 0
    ]


class Searcher:
    def __init__(
        self,
        stemmer: Stemmer,
        documents: list[Document],
    ):
        self._documents: dict[str, list[Document]] = {}
        for document in documents:
            self._documents.setdefault(document.language, []).append(document)
        self._idf = {
            language: _inverse_document_frequency(documents)
            for language, documents in self._documents.items()
        }
        self._vectors = {
            language: [
                _tf_idf_vector(document, self._idf[language])
                for document in documents
            ]
            for language, documents in self._documents.items()
        }
        self._stemmer = stemmer

    def search(
        self, query: str, language: str
    ) -> list[tuple[float, Document]]:
        return _search(
            query,
            language,
            self._vectors[language],
            self._idf[language],
            self._documents[language],
            self._stemmer,
        )
