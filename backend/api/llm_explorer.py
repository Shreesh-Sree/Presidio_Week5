"""AlgoQX Studio -- LLM Explorer API Endpoints."""

from fastapi import APIRouter, HTTPException
import numpy as np

from backend.models.schemas import (
    TokenizeRequest,
    TokenizeResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    SimilarityRequest,
    SimilarityResponse,
    CostEstimateRequest,
    CostEstimateResponse,
    ContextWindowRequest,
    ContextWindowResponse,
)
from backend.services import tokenizer_service, embedding_service, llm_service

router = APIRouter(prefix="/llm", tags=["LLM Explorer"])


@router.post("/tokenize", response_model=TokenizeResponse)
async def tokenize_text(request: TokenizeRequest):
    """Tokenize input text using tiktoken and return list of tokens with metadata."""
    try:
        tokens = tokenizer_service.tokenize(request.text, request.model)
        return TokenizeResponse(
            tokens=tokens,
            token_count=len(tokens),
            model=request.model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/count-tokens")
async def count_tokens(request: TokenizeRequest):
    """Count the total number of tokens in the input text."""
    try:
        count = tokenizer_service.count_tokens(request.text, request.model)
        return {"token_count": count, "model": request.model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/context-window", response_model=ContextWindowResponse)
async def context_window_analysis(request: ContextWindowRequest):
    """Analyze context window usage for a model."""
    try:
        limit = llm_service.get_context_window(request.model)
        analysis = tokenizer_service.analyze_context_window(
            request.text, request.model, limit
        )
        return ContextWindowResponse(
            model=analysis["model"],
            context_window=analysis["context_window"],
            used_tokens=analysis["used_tokens"],
            remaining_tokens=analysis["remaining_tokens"],
            usage_percent=analysis["usage_percent"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transformer-explanation")
async def transformer_explanation():
    """Return static conceptual explanation of Transformer architecture."""
    return {
        "title": "The Transformer Architecture",
        "description": "Transformers are the backbone of modern LLMs, introduced in 'Attention Is All You Need' (2017). They rely entirely on self-attention mechanisms to compute representations of input and output without using sequence-aligned RNNs or convolution.",
        "components": [
            {
                "name": "Tokenization",
                "role": "Converts raw text into numerical token IDs using a subword vocabulary.",
            },
            {
                "name": "Embedding Layer",
                "role": "Maps token IDs to high-dimensional continuous vectors representing semantic meaning.",
            },
            {
                "name": "Positional Encoding",
                "role": "Injects sequence order information into the embedding vectors since Attention itself is order-agnostic.",
            },
            {
                "name": "Multi-Head Self-Attention",
                "role": "Allows tokens to look at other tokens in the sequence to gather contextual clues. Multi-head means doing this in parallel subspaces.",
            },
            {
                "name": "Feed-Forward Networks (FFN)",
                "role": "Applies non-linear transformations to each token representation individually.",
            },
            {
                "name": "Layer Normalization & Residual Connections",
                "role": "Stops gradients from vanishing/exploding, helping train very deep networks.",
            },
            {
                "name": "Linear Output & Softmax",
                "role": "Projects the final layer vectors back to vocabulary size to compute next-token probabilities.",
            },
        ],
    }


@router.post("/embed", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """Generate high-dimensional vector representations for a list of texts."""
    try:
        embeddings = embedding_service.generate_embeddings(
            request.texts, request.model
        )
        return EmbeddingResponse(
            embeddings=embeddings.tolist(),
            dimensions=embeddings.shape[1],
            model=request.model,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity", response_model=SimilarityResponse)
async def calculate_similarity(request: SimilarityRequest):
    """Calculate cosine similarity between two texts."""
    try:
        similarity = embedding_service.compute_similarity(
            request.text_a, request.text_b, request.model
        )
        return SimilarityResponse(
            similarity=similarity,
            text_a=request.text_a,
            text_b=request.text_b,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attention-explanation")
async def attention_explanation():
    """Return static explanation of Self-Attention mathematical concept."""
    return {
        "title": "Self-Attention Mechanism",
        "formula": "Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V",
        "explanation": "Self-attention computes dynamic weights representing how much attention each word should pay to every other word in the sentence.",
        "steps": [
            {
                "step": 1,
                "name": "Projection",
                "description": "For each input vector, project it using learned weights into Query (Q), Key (K), and Value (V) vectors.",
            },
            {
                "step": 2,
                "name": "Query-Key Dot Product",
                "description": "Multiply Query vector of token A with Key vector of token B to get raw attention score.",
            },
            {
                "step": 3,
                "name": "Scaling",
                "description": "Divide dot products by the square root of key dimension (d_k) to prevent exploding values during softmax.",
            },
            {
                "step": 4,
                "name": "Softmax Normalization",
                "description": "Apply softmax to convert raw scores into probabilities summing to 1.0.",
            },
            {
                "step": 5,
                "name": "Weighted Value Sum",
                "description": "Multiply Value (V) vectors by attention probabilities and sum them up to produce the final representation.",
            },
        ],
    }


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(request: CostEstimateRequest):
    """Estimate financial cost based on token counts and target model."""
    try:
        input_tokens = tokenizer_service.count_tokens(request.text, "qwen2.5-7b-instruct:latest")
        input_cost = llm_service.estimate_cost(request.model, input_tokens, 0)
        output_cost = llm_service.estimate_cost(
            request.model, 0, request.expected_output_tokens
        )
        total_cost = input_cost + output_cost
        return CostEstimateResponse(
            model=request.model,
            input_tokens=input_tokens,
            output_tokens=request.expected_output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models():
    """List available LLM models."""
    try:
        models = await llm_service.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity-matrix")
async def similarity_matrix(texts: list[str], model: str = "qwen3-embedding:8b"):
    """Compute pairwise similarity matrix."""
    try:
        matrix = embedding_service.compute_similarity_matrix(texts, model)
        return {"matrix": matrix, "texts": texts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embedding-visualization")
async def embedding_visualization(
    texts: list[str],
    model: str = "BAAI/bge-small-en-v1.5",
    method: str = "pca",
    dimensions: int = 2,
):
    """Generate 2D or 3D coordinate mapping for a list of texts."""
    try:
        embeddings = embedding_service.generate_embeddings(texts, model)
        reduced = embedding_service.reduce_dimensions(
            embeddings, n_components=dimensions, method=method
        )
        coords = reduced.tolist()
        return {"coordinates": coords, "texts": texts, "dimensions": dimensions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
