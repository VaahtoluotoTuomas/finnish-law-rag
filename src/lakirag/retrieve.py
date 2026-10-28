"""Keyword (BM25), vector and hybrid retrieval over the passages."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from lakirag.text_fi import stem, tokenize

MODEL_NAME = "intfloat/multilingual-e5-small"
METHODS = ("bm25", "bm25-stem", "vector", "hybrid")
RRF_K = 60
# Hybrid search fuses this many top results from each method.
RRF_DEPTH = 50

# Takes a list of texts and returns one unit-length vector per text (rows of a matrix).
Encoder = Callable[[list[str]], np.ndarray]


def load_passages(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def top_k(scores: np.ndarray, k: int) -> list[int]:
    """Return the indices of the k highest scores, best first."""
    return [int(i) for i in np.argsort(-scores, kind="stable")[:k]]


def rrf(rankings: list[list[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: score(d) = sum of 1 / (k + rank of d), ranks starting at 1.

    Only ranks are used, so the methods' scores need not be on the same scale.
    """
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def e5_encoder(model_name: str = MODEL_NAME) -> Encoder:
    # Imported here because loading torch takes seconds and keyword search does not need it.
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)

    def encode(texts: list[str]) -> np.ndarray:
        return model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100,
        )

    return encode


def load_or_build_embeddings(passages: list[dict], encoder: Encoder, path: Path) -> np.ndarray:
    """Embed the passages, reusing the cached file if the passages have not changed."""
    key = hashlib.sha256(json.dumps(passages, ensure_ascii=False).encode()).hexdigest()
    if path.exists():
        cached = np.load(path)
        if str(cached["key"]) == key:
            return cached["embeddings"]
    # e5 models expect "passage: " before documents and "query: " before questions.
    embeddings = encoder([f"passage: {p['text']}" for p in passages])
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, embeddings=embeddings, key=key)
    return embeddings


class Retriever:
    def __init__(
        self,
        passages: list[dict],
        encoder: Encoder | None = None,
        embeddings: np.ndarray | None = None,
    ):
        self.passages = passages
        self.encoder = encoder
        self.embeddings = embeddings
        tokens = [tokenize(p["text"]) for p in passages]
        self.bm25 = BM25Okapi(tokens)
        self.bm25_stem = BM25Okapi([stem(t) for t in tokens])

    def scores(self, query: str, method: str) -> np.ndarray:
        """Return one score per passage; higher is better."""
        if method == "bm25":
            return self.bm25.get_scores(tokenize(query))
        if method == "bm25-stem":
            return self.bm25_stem.get_scores(stem(tokenize(query)))
        if method == "vector":
            if self.encoder is None or self.embeddings is None:
                raise ValueError("Vector search needs an encoder and embeddings")
            query_vector = self.encoder([f"query: {query}"])[0]
            # Both sides are unit vectors, so the dot product is the cosine similarity.
            return self.embeddings @ query_vector
        raise ValueError(f"Unknown method: {method}")

    def search(self, query: str, method: str = "hybrid", k: int = 5) -> list[tuple[dict, float]]:
        if method == "hybrid":
            rankings = [top_k(self.scores(query, m), RRF_DEPTH) for m in ("bm25-stem", "vector")]
            results = rrf(rankings)[:k]
        else:
            scores = self.scores(query, method)
            results = [(i, float(scores[i])) for i in top_k(scores, k)]
        return [(self.passages[i], score) for i, score in results]


def from_files(passages_path: Path, embeddings_path: Path, vectors: bool = True) -> Retriever:
    """Load the passages and, if vectors is True, the embedding model and embeddings."""
    passages = load_passages(passages_path)
    if not vectors:
        return Retriever(passages)
    encoder = e5_encoder()
    embeddings = load_or_build_embeddings(passages, encoder, embeddings_path)
    return Retriever(passages, encoder, embeddings)
