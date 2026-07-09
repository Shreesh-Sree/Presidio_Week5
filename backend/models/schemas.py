"""AlgoQX Studio -- Pydantic Request/Response Schemas."""

from __future__ import annotations

import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================
# Common
# ============================================================

class StatusResponse(BaseModel):
    status: str = "ok"
    message: str = ""


class ModelInfo(BaseModel):
    id: str
    name: str
    context_length: int = 0
    pricing_prompt: float = 0.0
    pricing_completion: float = 0.0


# ============================================================
# LLM Explorer
# ============================================================

class TokenizeRequest(BaseModel):
    text: str
    model: str = "qwen2.5-7b-instruct:latest"


class TokenizeResponse(BaseModel):
    tokens: list[dict[str, Any]]  # [{id, text, color}]
    token_count: int
    model: str


class EmbeddingRequest(BaseModel):
    texts: list[str]
    model: str = "qwen3-embedding:8b"


class EmbeddingResponse(BaseModel):
    embeddings: list[list[float]]
    dimensions: int
    model: str


class SimilarityRequest(BaseModel):
    text_a: str
    text_b: str
    model: str = "qwen3-embedding:8b"


class SimilarityResponse(BaseModel):
    similarity: float
    text_a: str
    text_b: str


class CostEstimateRequest(BaseModel):
    text: str
    model: str = "qwen2.5-7b-instruct:latest"
    expected_output_tokens: int = 500


class CostEstimateResponse(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


class ContextWindowRequest(BaseModel):
    text: str
    model: str = "qwen2.5-7b-instruct:latest"


class ContextWindowResponse(BaseModel):
    model: str
    context_window: int
    used_tokens: int
    remaining_tokens: int
    usage_percent: float


# ============================================================
# Prompt Lab
# ============================================================

class PromptCompareRequest(BaseModel):
    prompt: str
    model: str = "qwen2.5-7b-instruct:latest"
    strategies: list[str] = Field(
        default=[
            "zero_shot", "few_shot", "chain_of_thought",
            "role_prompt", "json_output", "xml_output", "system_prompt"
        ]
    )


class PromptResult(BaseModel):
    strategy: str
    response: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    quality_score: float = 0.0
    consistency_score: float = 0.0


class PromptCompareResponse(BaseModel):
    prompt: str
    model: str
    results: list[PromptResult]
    trace_id: str


# ============================================================
# RAG Studio
# ============================================================

class RAGUploadResponse(BaseModel):
    filename: str
    file_type: str
    chunk_count: int
    chunking_strategy: str
    embedding_model: str
    document_id: int


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    model: str = "qwen2.5-7b-instruct:latest"
    chunking_strategy: str = "recursive"
    embedding_model: str = "qwen3-embedding:8b"
    retriever_type: str = "similarity"  # similarity, mmr


class ChunkResult(BaseModel):
    content: str
    score: float
    rank: int
    metadata: dict[str, Any] = {}


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    chunks: list[ChunkResult]
    hallucination_score: float = 0.0
    groundedness_score: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    trace_id: str = ""


class RAGCompareResponse(BaseModel):
    query: str
    prompt_only: PromptResult
    rag_result: RAGQueryResponse
    comparison: dict[str, Any] = {}


# ============================================================
# Agent Builder
# ============================================================

class AgentNode(BaseModel):
    id: str
    type: str  # planner, researcher, retriever, reasoner, writer, reviewer
    label: str
    config: dict[str, Any] = {}
    position: dict[str, float] = {"x": 0, "y": 0}


class AgentEdge(BaseModel):
    source: str
    target: str
    label: str = ""
    condition: Optional[str] = None


class AgentConfig(BaseModel):
    nodes: list[AgentNode]
    edges: list[AgentEdge]
    tools: list[str] = []
    memory_enabled: bool = True
    human_approval: bool = False


class AgentExecuteRequest(BaseModel):
    config: AgentConfig
    input_text: str
    model: str = "qwen2.5-7b-instruct:latest"


class AgentStep(BaseModel):
    node_id: str
    node_type: str
    input_text: str
    output_text: str
    tokens: int = 0
    latency_ms: float = 0.0
    tool_calls: list[dict[str, Any]] = []
    status: str = "completed"


class AgentExecuteResponse(BaseModel):
    run_id: str
    output: str
    steps: list[AgentStep]
    execution_graph: dict[str, Any] = {}
    total_tokens: int = 0
    total_cost: float = 0.0
    latency_ms: float = 0.0
    status: str = "completed"


# ============================================================
# MCP
# ============================================================

class MCPToolInfo(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = {}


class MCPCallRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = {}
    server_type: str = "filesystem"


class MCPCallResponse(BaseModel):
    tool_name: str
    result: Any
    latency_ms: float = 0.0


# ============================================================
# App Builder
# ============================================================

class AppGenerateRequest(BaseModel):
    app_type: str  # chatbot, summarizer, document_qa, sentiment_analyzer
    model: str = "qwen2.5-7b-instruct:latest"
    include_rag: bool = False
    include_memory: bool = True


class AppGenerateResponse(BaseModel):
    app_type: str
    fastapi_code: str
    streamlit_code: str
    swagger_spec: dict[str, Any] = {}
    requirements: list[str] = []


# ============================================================
# Security
# ============================================================

class SecurityScanRequest(BaseModel):
    text: str
    scan_types: list[str] = Field(
        default=[
            "prompt_injection", "indirect_injection",
            "jailbreak", "system_prompt_leakage", "tool_misuse"
        ]
    )


class SecurityThreat(BaseModel):
    threat_type: str
    severity: str  # low, medium, high, critical
    confidence: float
    description: str
    matched_pattern: str = ""
    mitigation: str = ""


class SecurityScanResponse(BaseModel):
    input_text: str
    threats: list[SecurityThreat]
    is_safe: bool
    sanitized_text: str
    safe_response: str = ""
    risk_score: float = 0.0


class OWASPItem(BaseModel):
    id: str
    name: str
    description: str
    risk_level: str
    examples: list[str] = []
    mitigations: list[str] = []


# ============================================================
# Privacy
# ============================================================

class PrivacyScanRequest(BaseModel):
    text: str
    entity_types: list[str] = Field(
        default=[
            "EMAIL", "PHONE", "CREDIT_CARD", "API_KEY",
            "PASSWORD", "PAN", "AADHAAR", "PASSPORT"
        ]
    )
    mask_strategy: str = "redact"  # redact, hash, mask


class PIIEntity(BaseModel):
    entity_type: str
    value: str
    start: int
    end: int
    confidence: float
    masked_value: str


class PrivacyScanResponse(BaseModel):
    original_text: str
    masked_text: str
    entities: list[PIIEntity]
    entity_count: int
    explanation: str = ""


# ============================================================
# Observability
# ============================================================

class TraceStep(BaseModel):
    step_name: str
    step_type: str
    input_data: Any = None
    output_data: Any = None
    tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = {}
    timestamp: str = ""


class TraceResponse(BaseModel):
    trace_id: str
    module: str
    steps: list[TraceStep]
    total_tokens: int = 0
    total_cost: float = 0.0
    total_latency_ms: float = 0.0
    created_at: str = ""


# ============================================================
# Analytics
# ============================================================

class AnalyticsSummary(BaseModel):
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0
    avg_tokens: float = 0.0
    total_cost_usd: float = 0.0
    model_usage: dict[str, int] = {}
    prompt_style_usage: dict[str, int] = {}
    module_usage: dict[str, int] = {}
    security_threats: int = 0
    hallucination_rate: float = 0.0
    requests_over_time: list[dict[str, Any]] = []
    cost_over_time: list[dict[str, Any]] = []
