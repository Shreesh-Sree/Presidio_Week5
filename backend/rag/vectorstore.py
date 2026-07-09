"""AlgoQX Studio -- FAISS Vector Store.

Manages FAISS indices for document storage and retrieval.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any, Optional

import faiss
import numpy as np

from backend.config.settings import get_settings
from backend.services.embedding_service import generate_embeddings

settings = get_settings()

# In-memory store for document metadata (maps index position -> chunk data)
_metadata_store: dict[str, list[dict[str, Any]]] = {}
_indices: dict[str, faiss.Index] = {}


def create_index(
    chunks: list[dict[str, Any]],
    index_name: str = "default",
    model_name: str | None = None,
) -> dict[str, Any]:
    """Create a FAISS index from document chunks.

    Args:
        chunks: List of chunk dicts with 'content' key.
        index_name: Name for the index (for persistence).
        model_name: Embedding model to use.

    Returns:
        Dictionary with index stats.
    """
    texts = [c["content"] for c in chunks]
    embeddings = generate_embeddings(texts, model_name)

    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)  # Inner product (cosine sim with normalized vectors)
    index.add(np.array(embeddings).astype("float32"))

    _indices[index_name] = index
    _metadata_store[index_name] = chunks

    # Persist to disk
    _save_index(index_name)

    return {
        "index_name": index_name,
        "num_vectors": index.ntotal,
        "dimensions": d,
        "num_chunks": len(chunks),
    }


def search_index(
    query: str,
    index_name: str = "default",
    top_k: int = 5,
    model_name: str | None = None,
    retriever_type: str = "similarity",
) -> list[dict[str, Any]]:
    """Search the FAISS index for similar chunks.

    Args:
        query: Query text.
        index_name: Name of the index to search.
        top_k: Number of results to return.
        model_name: Embedding model for the query.
        retriever_type: 'similarity' or 'mmr'.

    Returns:
        List of result dicts with: content, score, rank, metadata.
    """
    index = _get_index(index_name)
    if index is None:
        return []

    query_embedding = generate_embeddings([query], model_name)
    query_vec = np.array(query_embedding).astype("float32")

    if retriever_type == "mmr":
        return _mmr_search(query_vec, index, index_name, top_k)

    distances, indices = index.search(query_vec, min(top_k, index.ntotal))
    metadata = _metadata_store.get(index_name, [])

    results = []
    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < 0:
            continue
        chunk = metadata[idx] if idx < len(metadata) else {"content": ""}
        results.append({
            "content": chunk.get("content", ""),
            "score": float(dist),
            "rank": rank + 1,
            "metadata": chunk.get("metadata", {}),
        })

    return results


def _mmr_search(
    query_vec: np.ndarray,
    index: faiss.Index,
    index_name: str,
    top_k: int,
    lambda_param: float = 0.5,
    fetch_k: int = 20,
) -> list[dict[str, Any]]:
    """Maximal Marginal Relevance search for diversity."""
    fetch_k = min(fetch_k, index.ntotal)
    distances, indices = index.search(query_vec, fetch_k)

    metadata = _metadata_store.get(index_name, [])
    candidates = list(zip(distances[0], indices[0]))

    selected = []
    selected_indices = set()

    for _ in range(min(top_k, len(candidates))):
        best_score = -float("inf")
        best_idx = -1

        for dist, idx in candidates:
            if idx in selected_indices or idx < 0:
                continue

            relevance = float(dist)
            diversity = 0.0
            if selected:
                diversity = min(
                    abs(float(dist) - s[0]) for s in selected
                )

            mmr_score = lambda_param * relevance + (1 - lambda_param) * diversity
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx >= 0:
            best_dist = next(d for d, i in candidates if i == best_idx)
            selected.append((float(best_dist), best_idx))
            selected_indices.add(best_idx)

    results = []
    for rank, (score, idx) in enumerate(selected):
        chunk = metadata[idx] if idx < len(metadata) else {"content": ""}
        results.append({
            "content": chunk.get("content", ""),
            "score": score,
            "rank": rank + 1,
            "metadata": chunk.get("metadata", {}),
        })

    return results


def _get_index(index_name: str) -> Optional[faiss.Index]:
    """Get an index from memory or load from disk."""
    if index_name in _indices:
        return _indices[index_name]

    index_path = Path(settings.faiss_index_path) / f"{index_name}.faiss"
    if index_path.exists():
        _indices[index_name] = faiss.read_index(str(index_path))
        meta_path = Path(settings.faiss_index_path) / f"{index_name}_meta.pkl"
        if meta_path.exists():
            with open(meta_path, "rb") as f:
                _metadata_store[index_name] = pickle.load(f)
        return _indices[index_name]

    return None


def _save_index(index_name: str) -> None:
    """Persist index and metadata to disk."""
    index_dir = Path(settings.faiss_index_path)
    index_dir.mkdir(parents=True, exist_ok=True)

    if index_name in _indices:
        faiss.write_index(_indices[index_name], str(index_dir / f"{index_name}.faiss"))

    if index_name in _metadata_store:
        with open(index_dir / f"{index_name}_meta.pkl", "wb") as f:
            pickle.dump(_metadata_store[index_name], f)


def list_indices() -> list[dict[str, Any]]:
    """List all available FAISS indices."""
    index_dir = Path(settings.faiss_index_path)
    indices = []

    if index_dir.exists():
        for f in index_dir.glob("*.faiss"):
            name = f.stem
            index = _get_index(name)
            if index:
                indices.append({
                    "name": name,
                    "num_vectors": index.ntotal,
                    "dimensions": index.d,
                })

    # Also include in-memory indices
    for name, index in _indices.items():
        if not any(i["name"] == name for i in indices):
            indices.append({
                "name": name,
                "num_vectors": index.ntotal,
                "dimensions": index.d,
            })

    return indices


def delete_index(index_name: str) -> bool:
    """Delete a FAISS index from memory and disk."""
    _indices.pop(index_name, None)
    _metadata_store.pop(index_name, None)

    index_dir = Path(settings.faiss_index_path)
    for ext in [".faiss", "_meta.pkl"]:
        path = index_dir / f"{index_name}{ext}"
        if path.exists():
            path.unlink()

    return True
