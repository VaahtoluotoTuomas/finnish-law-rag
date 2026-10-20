# Finnish Law RAG

[![CI](https://github.com/VaahtoluotoTuomas/finnish-law-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/VaahtoluotoTuomas/finnish-law-rag/actions/workflows/ci.yml)

A small retrieval-augmented generation (RAG) demo over two Finnish statutes: the Consumer Protection Act (*kuluttajansuojalaki* 38/1978) and the Insurance Contracts Act (*vakuutussopimuslaki* 543/1994). You ask a question in plain Finnish, the system retrieves the most relevant sections with keyword and vector search, and a language model answers from those sections only, citing them.

> Work in progress.

## How it works

_TODO: architecture diagram._

## Results

_TODO: retrieval evaluation table._

## Running locally

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

## Design decisions and limitations

_TODO._

## Data source

Finlex open data. Acts and decrees are not protected by copyright (Copyright Act 9 §).

## Tiivistelmä

_TODO: lyhyt suomenkielinen tiivistelmä._
