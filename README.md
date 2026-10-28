# Finnish Law RAG

[![CI](https://github.com/VaahtoluotoTuomas/finnish-law-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/VaahtoluotoTuomas/finnish-law-rag/actions/workflows/ci.yml)

A small retrieval-augmented generation (RAG) project over two Finnish laws: the Consumer Protection Act (*kuluttajansuojalaki* 38/1978) and the Insurance Contracts Act (*vakuutussopimuslaki* 543/1994).

The idea: you ask something in plain Finnish ("Saanko palauttaa netistä ostetun takin?"), the system finds the relevant sections of law, and a language model answers from those sections only, citing them.

> 🚧 **Work in progress.** This is a learning project I'm building step by step. Search works; measuring it and generating answers come next.

## What works so far

- **Data:** downloads both laws from the Finlex open data API and splits them into 485 passages, one per section (very long sections are split by subsection). Repealed sections are dropped, and where Finlex shows both an old and an upcoming wording, the newer one is used.
- **Search:** four ways to find sections, so they can be compared:
  - `bm25`: plain keyword search
  - `bm25-stem`: keyword search with Finnish stemming
  - `vector`: semantic search with the [`multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small) embedding model
  - `hybrid`: stemmed BM25 and vector search combined with Reciprocal Rank Fusion

No LangChain or vector database: a few hundred passages fit fine in a numpy array, and writing the pieces by hand is the point.

## Try it

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e ".[dev]"

python -m lakirag search "Voinko perua verkkokaupasta tehdyn tilauksen?" --method all
```

The first vector search downloads the model (~0.5 GB) and embeds all passages, which takes a minute. After that it's quick.

Other commands: `python -m lakirag fetch` re-downloads the laws, and `python -m lakirag build` rebuilds `data/passages.jsonl`. Run `pytest` for the tests.

## Early observations

Finnish is hard for keyword search. The law says *peruuttaa* and *etämyynti*, but people say *palauttaa* and *netistä*. Stemming only helps a little: the Snowball stemmer joins *palauttaa* and *palautin*, but treats *vakuutus*, *vakuutuksen* and *vakuutusta* as three different words. Vector search copes better with paraphrases. Proper numbers will follow once there's a test set.

## Next up

- [ ] A test set of ~30 questions, with recall@k and MRR for each search method
- [ ] Answers from Claude based on the retrieved sections, with citations and a refusal when the laws don't cover the question
- [ ] Retrieval evaluation as a CI gate, prompt versioning and query logging

## Notes and limitations

- The text is the Finlex consolidated version of 4 September 2026. In chapters 7 and 7 a of the Consumer Protection Act, the wording that enters into force on 20 November 2026 is used, and a few points already use wording from July 2027.
- Nothing here is legal advice.
- Data: Finlex open data. Acts and decrees are not protected by copyright (Copyright Act 9 §).

## Suomeksi lyhyesti

Harjoitusprojekti, jossa rakennan pienen RAG-järjestelmän kuluttajansuojalaista ja vakuutussopimuslaista. Lait haetaan Finlexin avoimesta rajapinnasta ja pilkotaan pykäliksi, ja hakua voi kokeilla neljällä tavalla: avainsanahaku, stemmattu avainsanahaku, vektorihaku ja näiden yhdistelmä. Seuraavaksi mitataan, mikä haku toimii parhaiten, ja lisätään kielimallin vastaukset pykäläviittein. Työ on vielä kesken.
