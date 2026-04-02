"""Chroma-backed retrieval over Nigerian Finance Act text (deterministic; no LLM)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CHROMA_PATH = _REPO_ROOT / ".cache" / "chroma_tax_law"
_FINANCE_ACTS_DIR = _REPO_ROOT / "data" / "finance_acts"

_COLLECTION_NAME = "nigerian_finance_acts"
_EMBED_MODEL = os.environ.get("CHROMA_EMBED_MODEL", "all-MiniLM-L6-v2")

_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None
_embedding_fn: Any = None


def _get_embedding_function() -> Any:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=_EMBED_MODEL
        )
    return _embedding_fn


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is not None:
        return _collection
    _CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    _client = chromadb.PersistentClient(path=str(_CHROMA_PATH))
    _collection = _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=_get_embedding_function(),
    )
    return _collection


def _chunk_text(text: str, *, size: int = 900, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + size])
        i += size - overlap
        if i >= len(text):
            break
    return chunks


def _ingest_finance_act_files_if_empty() -> None:
    coll = _get_collection()
    if coll.count() > 0:
        return
    if not _FINANCE_ACTS_DIR.is_dir():
        return
    blobs: list[str] = []
    for path in sorted(_FINANCE_ACTS_DIR.glob("*.txt")):
        if path.name.upper().startswith("README"):
            continue
        try:
            blobs.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    combined = "\n\n".join(blobs)
    if not combined.strip():
        return
    chunks = _chunk_text(combined)
    if not chunks:
        return
    ids = [f"fin_act_{i}" for i in range(len(chunks))]
    metadatas = [{"source": "data/finance_acts"} for _ in chunks]
    coll.add(ids=ids, documents=chunks, metadatas=metadatas)


def query_tax_law(query: str, top_k: int = 5) -> dict[str, Any]:
    """
    Retrieve relevant tax-law snippets for a natural-language query.

    Uses Chroma persistent storage under ``.cache/chroma_tax_law`` and ingests
    ``data/finance_acts/*.txt`` once when the collection is empty.
    """
    q = (query or "").strip()
    if not q:
        return {
            "status": "empty_query",
            "chunks": [],
            "detail": "Provide a non-empty query string.",
        }

    try:
        _ingest_finance_act_files_if_empty()
        coll = _get_collection()
    except Exception as e:
        return {
            "status": "error",
            "chunks": [],
            "detail": f"Chroma setup failed: {e}",
            "query_preview": q[:200],
        }

    if coll.count() == 0:
        return {
            "status": "empty_collection",
            "chunks": [],
            "detail": (
                "No Finance Act text indexed. Add ``.txt`` sources under "
                "data/finance_acts/ (see data/finance_acts/README.md), then "
                "clear .cache/chroma_tax_law to re-ingest."
            ),
            "query_preview": q[:200],
        }

    k = max(1, min(int(top_k), 50))
    try:
        res = coll.query(query_texts=[q], n_results=k)
    except Exception as e:
        return {
            "status": "error",
            "chunks": [],
            "detail": str(e),
            "query_preview": q[:200],
        }

    docs = (res.get("documents") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]

    chunks_out: list[dict[str, Any]] = []
    for i, doc in enumerate(docs):
        chunks_out.append(
            {
                "text": doc,
                "distance": dists[i] if i < len(dists) else None,
                "metadata": metas[i] if i < len(metas) else {},
            }
        )

    return {
        "status": "ok",
        "chunks": chunks_out,
        "query_preview": q[:200],
    }
