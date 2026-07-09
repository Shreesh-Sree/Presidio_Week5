"""AlgoQX Studio -- Text Chunking Strategies.

Provides multiple chunking approaches for document splitting.
"""

from __future__ import annotations

from typing import Any


def chunk_text(
    text: str,
    strategy: str = "recursive",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Split text into chunks using the specified strategy.

    Args:
        text: The full document text.
        strategy: Chunking strategy ('recursive', 'fixed_size', 'sentence', 'semantic').
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.
        metadata: Additional metadata to attach to each chunk.

    Returns:
        List of chunk dicts with keys: content, index, start, end, metadata.
    """
    strategies = {
        "recursive": _recursive_chunk,
        "fixed_size": _fixed_size_chunk,
        "sentence": _sentence_chunk,
        "semantic": _semantic_chunk,
    }

    chunker = strategies.get(strategy, _recursive_chunk)
    raw_chunks = chunker(text, chunk_size, chunk_overlap)

    return [
        {
            "content": chunk,
            "index": i,
            "start": text.find(chunk[:50]),
            "end": text.find(chunk[:50]) + len(chunk),
            "metadata": {**(metadata or {}), "chunk_strategy": strategy, "chunk_index": i},
        }
        for i, chunk in enumerate(raw_chunks)
    ]


def _recursive_chunk(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Recursively split text using hierarchical separators."""
    separators = ["\n\n", "\n", ". ", " ", ""]
    return _split_recursive(text, separators, chunk_size, chunk_overlap)


def _split_recursive(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Internal recursive splitting logic."""
    chunks: list[str] = []

    if len(text) <= chunk_size:
        if text.strip():
            chunks.append(text.strip())
        return chunks

    separator = separators[0]
    remaining_separators = separators[1:] if len(separators) > 1 else separators

    if separator:
        parts = text.split(separator)
    else:
        # Character-level split as fallback
        parts = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]
        return [p.strip() for p in parts if p.strip()]

    current_chunk: list[str] = []
    current_length = 0

    for part in parts:
        part_length = len(part) + len(separator)

        if current_length + part_length > chunk_size and current_chunk:
            chunk_text = separator.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

            # Calculate overlap
            overlap_parts: list[str] = []
            overlap_length = 0
            for prev_part in reversed(current_chunk):
                if overlap_length + len(prev_part) > chunk_overlap:
                    break
                overlap_parts.insert(0, prev_part)
                overlap_length += len(prev_part) + len(separator)

            current_chunk = overlap_parts + [part]
            current_length = sum(len(p) for p in current_chunk) + len(separator) * (len(current_chunk) - 1)
        else:
            current_chunk.append(part)
            current_length += part_length

    if current_chunk:
        chunk_text = separator.join(current_chunk).strip()
        if chunk_text:
            if len(chunk_text) > chunk_size and remaining_separators != separators:
                chunks.extend(_split_recursive(chunk_text, remaining_separators, chunk_size, chunk_overlap))
            else:
                chunks.append(chunk_text)

    return chunks


def _fixed_size_chunk(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap
    return chunks


def _sentence_chunk(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text by sentences, grouping into chunks."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk: list[str] = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep last sentence for overlap
            overlap_text = current_chunk[-1] if current_chunk else ""
            current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
            current_length = sum(len(s) for s in current_chunk)
        else:
            current_chunk.append(sentence)
            current_length += len(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return [c.strip() for c in chunks if c.strip()]


def _semantic_chunk(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text at paragraph boundaries (semantic chunking approximation)."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk: list[str] = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if current_length + len(para) > chunk_size and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_length = len(para)
        else:
            current_chunk.append(para)
            current_length += len(para)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return [c.strip() for c in chunks if c.strip()]
