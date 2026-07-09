"""AlgoQX Studio -- Tokenizer Service.

Provides tokenization, token counting, and context window analysis.
"""

from __future__ import annotations

import hashlib
from typing import Any

import tiktoken

# Color palette for token visualization
TOKEN_COLORS = [
    "#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#ec4899", "#14b8a6", "#f97316", "#3b82f6",
    "#a855f7", "#22c55e", "#e11d48", "#0ea5e9", "#d946ef",
]


def get_encoding(model: str = "qwen2.5-7b-instruct:latest") -> tiktoken.Encoding:
    """Get the tiktoken encoding for a model."""
    try:
        # Map Ollama models to tiktoken encodings
        if "qwen" in model or "llama" in model:
            return tiktoken.get_encoding("cl100k_base")
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def tokenize(text: str, model: str = "qwen2.5-7b-instruct:latest") -> list[dict[str, Any]]:
    """Tokenize text and return detailed token information.

    Returns:
        List of dicts with keys: id, text, index, color, byte_length
    """
    encoding = get_encoding(model)
    token_ids = encoding.encode(text)
    tokens = []

    for i, token_id in enumerate(token_ids):
        token_bytes = encoding.decode_single_token_bytes(token_id)
        token_text = token_bytes.decode("utf-8", errors="replace")
        color_index = hash(token_text.strip()) % len(TOKEN_COLORS)
        tokens.append({
            "id": token_id,
            "text": token_text,
            "index": i,
            "color": TOKEN_COLORS[color_index],
            "byte_length": len(token_bytes),
        })

    return tokens


def count_tokens(text: str, model: str = "qwen2.5-7b-instruct:latest") -> int:
    """Count the number of tokens in text."""
    encoding = get_encoding(model)
    return len(encoding.encode(text))


def count_message_tokens(
    messages: list[dict[str, str]],
    model: str = "qwen2.5-7b-instruct:latest",
) -> int:
    """Count tokens in a list of chat messages (including overhead)."""
    encoding = get_encoding(model)
    tokens_per_message = 3  # <|start|>{role}\n{content}<|end|>\n
    total = 0
    for msg in messages:
        total += tokens_per_message
        for key, value in msg.items():
            total += len(encoding.encode(value))
    total += 3  # reply priming
    return total


def analyze_context_window(
    text: str,
    model: str = "qwen2.5-7b-instruct:latest",
    context_window: int = 131072,
) -> dict[str, Any]:
    """Analyze how much of the context window is used.

    Returns:
        Dictionary with used_tokens, remaining, percentage, etc.
    """
    used = count_tokens(text, model)
    remaining = max(0, context_window - used)
    percentage = (used / context_window * 100) if context_window > 0 else 0

    return {
        "model": model,
        "context_window": context_window,
        "used_tokens": used,
        "remaining_tokens": remaining,
        "usage_percent": round(percentage, 2),
        "status": "ok" if percentage < 80 else ("warning" if percentage < 95 else "critical"),
    }


def get_vocabulary_info(model: str = "gpt-3.5-turbo") -> dict[str, Any]:
    """Get vocabulary information for a model's tokenizer."""
    encoding = get_encoding(model)
    return {
        "encoding_name": encoding.name,
        "vocab_size": encoding.n_vocab,
        "special_tokens": len(encoding.special_tokens_set),
    }
