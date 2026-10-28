from pathlib import Path

import numpy as np
import pytest

from lakirag import retrieve
from lakirag.cli import main
from lakirag.text_fi import stem, tokenize

PASSAGES_PATH = Path(__file__).parent.parent / "data" / "passages.jsonl"

PASSAGES = [
    {"id": "A", "title": "Palautus", "text": "Kuluttaja saa palauttaa tavaran 14 päivän kuluessa."},
    {"id": "B", "title": "Vakuutus", "text": "Vakuutuksenottajan on maksettava vakuutusmaksu."},
    {"id": "C", "title": "Virhe", "text": "Tavarassa on virhe, jos se ei vastaa sopimusta."},
]
VOCABULARY = ["palau", "vakuut", "virhe"]


def fake_encoder(texts: list[str]) -> np.ndarray:
    """Count a few word stems per text and normalise, so tests need no model download."""
    vectors = np.array(
        [[text.lower().count(word) for word in VOCABULARY] for text in texts], dtype=float
    )
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1, norms)


@pytest.fixture
def retriever():
    embeddings = fake_encoder([p["text"] for p in PASSAGES])
    return retrieve.Retriever(PASSAGES, fake_encoder, embeddings)


def test_tokenize_lowercases_and_drops_punctuation():
    assert tokenize("Peruuttamisoikeus (6 luvun 14 §).") == [
        "peruuttamisoikeus",
        "6",
        "luvun",
        "14",
    ]


def test_stemming_joins_inflected_forms():
    assert len(set(stem(["palauttaa", "palautin", "palautan"]))) == 1
    assert len(set(stem(["tavara", "tavaran"]))) == 1


def test_stemming_is_not_perfect():
    # Snowball only cuts endings: consonant gradation and derivations stay apart.
    assert len(set(stem(["vakuutus", "vakuutuksen", "vakuutusta"]))) == 3
    assert stem(["palautus"]) != stem(["palauttaa"])


def test_cosine_similarity():
    v = np.array([1.0, 2.0, 3.0])
    assert retrieve.cosine_similarity(v, v) == pytest.approx(1.0)
    assert retrieve.cosine_similarity(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 0.0


def test_top_k_returns_best_first():
    assert retrieve.top_k(np.array([0.1, 0.9, 0.5]), 2) == [1, 2]


def test_rrf_by_hand():
    # Doc 0: 1/(60+1) + 1/(60+2), doc 1: 1/(60+2) + 1/(60+1), doc 2: 1/(60+3) only.
    fused = retrieve.rrf([[0, 1, 2], [1, 0]])
    assert [doc for doc, _ in fused][2] == 2
    assert dict(fused)[0] == pytest.approx(1 / 61 + 1 / 62)
    assert dict(fused)[2] == pytest.approx(1 / 63)


@pytest.mark.parametrize("method", retrieve.METHODS)
def test_search_returns_k_results(retriever, method):
    assert len(retriever.search("palautus", method, k=2)) == 2


def test_stemming_finds_inflected_query(retriever):
    assert retriever.scores("palautin", "bm25").max() == 0
    [(passage, _)] = retriever.search("palautin", "bm25-stem", k=1)
    assert passage["id"] == "A"


def test_vector_and_hybrid_search(retriever):
    assert retriever.search("vakuutusmaksu", "vector", k=1)[0][0]["id"] == "B"
    assert retriever.search("vakuutusmaksu", "hybrid", k=1)[0][0]["id"] == "B"


def test_vector_search_needs_embeddings():
    with pytest.raises(ValueError):
        retrieve.Retriever(PASSAGES).search("palautus", "vector")


def test_embeddings_are_cached(tmp_path):
    calls = []

    def counting_encoder(texts):
        calls.append(texts)
        return fake_encoder(texts)

    path = tmp_path / "embeddings.npz"
    first = retrieve.load_or_build_embeddings(PASSAGES, counting_encoder, path)
    second = retrieve.load_or_build_embeddings(PASSAGES, counting_encoder, path)
    assert len(calls) == 1
    assert calls[0][0].startswith("passage: ")
    np.testing.assert_allclose(first, second)

    retrieve.load_or_build_embeddings(PASSAGES[:2], counting_encoder, path)
    assert len(calls) == 2


def test_cli_search_bm25(monkeypatch, capsys):
    monkeypatch.setattr("lakirag.cli.PASSAGES_PATH", PASSAGES_PATH)
    assert main(["search", "peruuttamisoikeus etämyynti", "--method", "bm25-stem", "-k", "3"]) == 0
    out = capsys.readouterr().out
    assert "bm25-stem:" in out
    assert out.count(". KSL") + out.count(". VSL") == 3
