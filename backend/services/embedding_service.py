"""AlgoQX Studio -- Embedding Service.

Manages sentence-transformer models for embedding generation
and similarity computation.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from backend.config.settings import get_settings

settings = get_settings()

# Model cache
_models: dict[str, SentenceTransformer] = {}


def get_embedding_model(model_name: str | None = None) -> SentenceTransformer:
    """Load and cache a sentence-transformer model."""
    name = model_name or settings.embedding_model
    if name not in _models:
        _models[name] = SentenceTransformer(name)
    return _models[name]


def generate_embeddings(
    texts: list[str],
    model_name: str | None = None,
    normalize: bool = True,
) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of strings to embed.
        model_name: Model identifier (defaults to config).
        normalize: Whether to L2-normalize embeddings.

    Returns:
        numpy array of shape (len(texts), embedding_dim).
    """
    model = get_embedding_model(model_name)
    embeddings = model.encode(
        texts,
        normalize_embeddings=normalize,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return embeddings


def compute_similarity(
    text_a: str,
    text_b: str,
    model_name: str | None = None,
) -> float:
    """Compute cosine similarity between two texts."""
    model = get_embedding_model(model_name)
    emb_a = model.encode([text_a], normalize_embeddings=True, convert_to_numpy=True)
    emb_b = model.encode([text_b], normalize_embeddings=True, convert_to_numpy=True)
    similarity = cos_sim(emb_a, emb_b)
    return float(similarity[0][0])


def compute_similarity_matrix(
    texts: list[str],
    model_name: str | None = None,
) -> list[list[float]]:
    """Compute pairwise similarity matrix for a list of texts."""
    model = get_embedding_model(model_name)
    embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    sim_matrix = cos_sim(embeddings, embeddings)
    return sim_matrix.tolist()


def reduce_dimensions(
    embeddings: np.ndarray,
    n_components: int = 2,
    method: str = "pca",
) -> np.ndarray:
    """Reduce embedding dimensions for visualization.

    Args:
        embeddings: High-dimensional embeddings.
        n_components: Target dimensions (2 or 3).
        method: Reduction method ('pca' or 'tsne').

    Returns:
        Reduced embeddings array.
    """
    if method == "tsne":
        from sklearn.manifold import TSNE
        reducer = TSNE(
            n_components=n_components,
            random_state=42,
            perplexity=min(30, len(embeddings) - 1) if len(embeddings) > 1 else 1,
        )
    else:
        from sklearn.decomposition import PCA
        reducer = PCA(n_components=n_components, random_state=42)

    return reducer.fit_transform(embeddings)


def get_model_info(model_name: str | None = None) -> dict:
    """Get information about the embedding model."""
    model = get_embedding_model(model_name)
    return {
        "model_name": model_name or settings.embedding_model,
        "max_seq_length": model.max_seq_length,
        "embedding_dimension": model.get_sentence_embedding_dimension(),
    }
