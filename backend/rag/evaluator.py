"""AlgoQX Studio -- RAG Evaluator.

Evaluates RAG pipeline quality with hallucination and groundedness scoring.
"""

from __future__ import annotations

from typing import Any

from backend.services.embedding_service import compute_similarity


def evaluate_response(
    query: str,
    response: str,
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate a RAG response for quality metrics.

    Args:
        query: Original user query.
        response: LLM-generated response.
        retrieved_chunks: List of retrieved chunk dicts with 'content' key.

    Returns:
        Dictionary with hallucination_score, groundedness_score, and other metrics.
    """
    if not retrieved_chunks or not response:
        return {
            "hallucination_score": 0.5,
            "groundedness_score": 0.5,
            "relevance_score": 0.0,
            "faithfulness_score": 0.0,
            "details": "No chunks or response to evaluate.",
        }

    # Compute groundedness: similarity between response and context
    context = " ".join(c.get("content", "") for c in retrieved_chunks)
    groundedness = compute_similarity(response, context)

    # Compute relevance: similarity between query and response
    relevance = compute_similarity(query, response)

    # Compute faithfulness: average similarity of response to each chunk
    chunk_similarities = []
    for chunk in retrieved_chunks:
        sim = compute_similarity(response, chunk.get("content", ""))
        chunk_similarities.append(sim)
    faithfulness = sum(chunk_similarities) / len(chunk_similarities) if chunk_similarities else 0

    # Hallucination score: inverse of groundedness (higher = more hallucination)
    hallucination = max(0, 1.0 - groundedness)

    return {
        "hallucination_score": round(hallucination, 4),
        "groundedness_score": round(groundedness, 4),
        "relevance_score": round(relevance, 4),
        "faithfulness_score": round(faithfulness, 4),
        "chunk_similarities": [round(s, 4) for s in chunk_similarities],
        "details": _interpret_scores(hallucination, groundedness, relevance),
    }


def compare_approaches(
    query: str,
    prompt_only_response: str,
    rag_response: str,
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare prompt-only vs RAG responses.

    Returns comparison data and recommendation.
    """
    prompt_relevance = compute_similarity(query, prompt_only_response)
    rag_relevance = compute_similarity(query, rag_response)

    rag_eval = evaluate_response(query, rag_response, retrieved_chunks)

    comparison = {
        "prompt_only": {
            "relevance": round(prompt_relevance, 4),
            "groundedness": 0.0,  # No grounding source for prompt-only
            "hallucination_risk": "high",
        },
        "rag": {
            "relevance": round(rag_relevance, 4),
            "groundedness": rag_eval["groundedness_score"],
            "hallucination_risk": _risk_level(rag_eval["hallucination_score"]),
        },
        "recommendation": _get_recommendation(prompt_relevance, rag_relevance, rag_eval),
        "fine_tuning": {
            "description": (
                "Fine-tuning is recommended when you need consistent domain-specific behavior, "
                "have a large labeled dataset, and the knowledge is relatively static. "
                "It bakes knowledge into model weights rather than retrieving it at inference time."
            ),
            "when_to_use": [
                "Large consistent training dataset available",
                "Domain-specific terminology or style needed",
                "Low-latency requirements (no retrieval overhead)",
                "Static knowledge base that rarely changes",
            ],
            "when_not_to_use": [
                "Knowledge changes frequently",
                "Need to cite sources",
                "Limited training data",
                "Need transparency in reasoning",
            ],
        },
    }

    return comparison


def _interpret_scores(hallucination: float, groundedness: float, relevance: float) -> str:
    """Generate a human-readable interpretation of the scores."""
    parts = []

    if groundedness > 0.7:
        parts.append("The response is well-grounded in the retrieved context.")
    elif groundedness > 0.4:
        parts.append("The response is partially grounded. Some content may extend beyond the sources.")
    else:
        parts.append("The response shows low groundedness. Much of the content may not be from the sources.")

    if hallucination < 0.3:
        parts.append("Low hallucination risk.")
    elif hallucination < 0.6:
        parts.append("Moderate hallucination risk. Verify key claims.")
    else:
        parts.append("High hallucination risk. Cross-check all claims against sources.")

    if relevance > 0.6:
        parts.append("The response is relevant to the query.")
    else:
        parts.append("The response may not fully address the query.")

    return " ".join(parts)


def _risk_level(score: float) -> str:
    """Convert a numeric score to a risk level string."""
    if score < 0.3:
        return "low"
    elif score < 0.6:
        return "medium"
    return "high"


def _get_recommendation(
    prompt_relevance: float,
    rag_relevance: float,
    rag_eval: dict[str, Any],
) -> str:
    """Generate a recommendation on which approach to use."""
    if rag_eval["groundedness_score"] > 0.6 and rag_relevance > prompt_relevance:
        return (
            "RAG is recommended for this use case. The retrieved context provides "
            "grounding that reduces hallucination and improves factual accuracy."
        )
    elif prompt_relevance > 0.7:
        return (
            "For this query, prompt-only may be sufficient as the model has "
            "strong inherent knowledge. Consider RAG for domain-specific or "
            "frequently updated information."
        )
    else:
        return (
            "Consider improving your RAG pipeline (better chunking, more documents) "
            "or using fine-tuning for this domain."
        )
