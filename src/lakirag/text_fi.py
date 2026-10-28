"""Finnish tokenisation and stemming for keyword search."""

import re

import snowballstemmer

WORD = re.compile(r"\w+")
STEMMER = snowballstemmer.stemmer("finnish")


def tokenize(text: str) -> list[str]:
    """Lowercase and split into words, dropping punctuation and symbols like §."""
    return WORD.findall(text.lower())


def stem(tokens: list[str]) -> list[str]:
    """Cut inflection endings so that e.g. 'palauttaa' and 'palautin' share a stem."""
    return STEMMER.stemWords(tokens)
