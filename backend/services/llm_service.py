"""AlgoQX Studio -- LLM Service.

Handles all LLM interactions via the self-hosted Ollama endpoint
using the OpenAI-compatible API.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from openai import AsyncOpenAI

from backend.config.settings import get_settings

settings = get_settings()

# Global async client -- reused across requests
_client: Optional[AsyncOpenAI] = None


def get_llm_client() -> AsyncOpenAI:
    """Get or create the async OpenAI client pointed at Ollama."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
    return _client


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    response_format: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Send a chat completion request and return structured result.

    Returns:
        Dictionary with keys: response, input_tokens, output_tokens,
        total_tokens, latency_ms, model
    """
    client = get_llm_client()
    model = model or settings.llm_default_model

    start = time.perf_counter()
    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        completion = await client.chat.completions.create(**kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000

        usage = completion.usage
        return {
            "response": completion.choices[0].message.content or "",
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
            "latency_ms": round(elapsed_ms, 2),
            "model": model,
            "finish_reason": completion.choices[0].finish_reason,
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "response": f"Error: {str(e)}",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": round(elapsed_ms, 2),
            "model": model,
            "finish_reason": "error",
            "error": str(e),
        }


async def list_models() -> list[dict[str, Any]]:
    """List available models from the Ollama endpoint."""
    client = get_llm_client()
    try:
        models = await client.models.list()
        return [
            {
                "id": m.id,
                "name": m.id,
                "owned_by": getattr(m, "owned_by", "ollama"),
            }
            for m in models.data
        ]
    except Exception:
        # Fallback with known models
        return [
            {"id": "llama3.2:3b", "name": "Llama 3.2 3B", "owned_by": "meta"},
            {"id": "qwen3-embedding:8b", "name": "Qwen3 8B", "owned_by": "alibaba"},
            {"id": "qwen3.6:35b", "name": "Qwen3 35B", "owned_by": "alibaba"},
            {"id": "qwen2.5-7b-instruct:latest", "name": "Qwen2.5 7B Instruct", "owned_by": "alibaba"},
            {"id": "test-qwen-fast:latest", "name": "Test Qwen Fast", "owned_by": "alibaba"},
            {"id": "qwen3.5:122b", "name": "Qwen3 122B", "owned_by": "alibaba"},
        ]


async def streaming_chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
):
    """Stream a chat completion response token by token.

    Yields:
        String chunks of the response.
    """
    client = get_llm_client()
    model = model or settings.llm_default_model

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


# -- Cost calculation (approximate for self-hosted) --

MODEL_COSTS: dict[str, dict[str, float]] = {
    "llama3.2:3b": {"prompt": 0.0000004, "completion": 0.0000012},
    "qwen3-embedding:8b": {"prompt": 0.0000003, "completion": 0.000001},
    "qwen3.6:35b": {"prompt": 0.000003, "completion": 0.000009},
    "qwen2.5-7b-instruct:latest": {"prompt": 0.0000008, "completion": 0.0000024},
    "test-qwen-fast:latest": {"prompt": 0.0000002, "completion": 0.0000006},
    "qwen3.5:122b": {"prompt": 0.000005, "completion": 0.000015},
}

# Context window sizes per model
CONTEXT_WINDOWS: dict[str, int] = {
    "llama3.2:3b": 131072,
    "qwen2.5-7b-instruct:latest": 131072,
    "qwen3.6:35b": 131072,
    "qwen3.5:122b": 200000,
    "qwen3-embedding:8b": 32768,
    "test-qwen-fast:latest": 32768,
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a given model and token counts."""
    costs = MODEL_COSTS.get(model, {"prompt": 0.0000005, "completion": 0.0000015})
    return (input_tokens * costs["prompt"]) + (output_tokens * costs["completion"])


def get_context_window(model: str) -> int:
    """Get the context window size for a model."""
    return CONTEXT_WINDOWS.get(model, 8192)
