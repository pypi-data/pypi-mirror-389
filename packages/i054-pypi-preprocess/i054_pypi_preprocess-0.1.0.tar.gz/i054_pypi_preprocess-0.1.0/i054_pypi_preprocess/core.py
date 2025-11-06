"""Tiny, dependency-free NLP preprocessing helpers."""

import re
from typing import List, Iterable, Set

_DEFAULT_STOPWORDS = {
    "a", "an", "the", "in", "on", "and", "or", "is", "are",
    "was", "were", "to", "of", "for", "with", "that", "this", "it"
}

def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip."""
    return re.sub(r"\s+", " ", text.strip().lower())

def remove_punct(text: str) -> str:
    """Remove punctuation (keep alphanumerics and whitespace)."""
    return re.sub(r"[^\w\s]", "", text)

def tokenize_simple(text: str) -> List[str]:
    """Normalize, remove punctuation, split on whitespace."""
    cleaned = remove_punct(normalize_text(text))
    return cleaned.split() if cleaned else []

def remove_stopwords(tokens: Iterable[str], stopwords: Set[str] | None = None) -> List[str]:
    """Remove stopwords (defaults to a small built-in set)."""
    stop = stopwords or _DEFAULT_STOPWORDS
    return [t for t in tokens if t not in stop]

def preprocess(text: str, stopwords: Set[str] | None = None) -> List[str]:
    """Full mini-pipeline: normalize → tokenize → remove stopwords."""
    tokens = tokenize_simple(text)
    return remove_stopwords(tokens, stopwords)
