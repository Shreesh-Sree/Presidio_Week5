"""AlgoQX Studio -- Prompt Lab API Endpoints."""

import asyncio
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db
from backend.database.models import PromptVersion
from backend.models.schemas import (
    PromptCompareRequest,
    PromptCompareResponse,
    PromptResult,
)
from backend.services import llm_service, observability_service

router = APIRouter(prefix="/prompt", tags=["Prompt Lab"])

# Predefined strategies guidelines/templates
STRATEGY_TEMPLATES = {
    "few_shot": (
        "Here are examples of how to respond:\n"
        "Input: Hello\n"
        "Output: Greeting received. How may I assist you today?\n"
        "Input: What is the capital of France?\n"
        "Output: The capital of France is Paris.\n"
        "Input: {prompt}\n"
        "Output:"
    ),
    "chain_of_thought": (
        "Solve the following query by thinking step-by-step. Show your reasoning steps clearly.\n"
        "Query: {prompt}\n"
        "Reasoning:"
    ),
    "role_prompt": {
        "system": "You are a distinguished Principal AI Architect, known for precise, logical, and technically robust answers.",
        "user": "{prompt}",
    },
    "json_output": (
        "Respond to the following request. Your output MUST be a valid JSON object. "
        "Do not include any pre-text or post-text explanation.\n"
        "Request: {prompt}"
    ),
    "xml_output": (
        "Respond to the following request. Wrap your response inside an <xml><output>...</output></xml> structure.\n"
        "Request: {prompt}"
    ),
    "system_prompt": {
        "system": "You are a helpful assistant. Always follow these rules:\n1. Be factual and exact.\n2. Be structured.",
        "user": "{prompt}",
    },
}


def _calculate_quality(response: str, strategy: str) -> float:
    """Calculate a heuristic quality score for the response (0.0 to 100.0)."""
    score = 50.0  # Base score

    if not response or len(response.strip()) == 0:
        return 0.0

    # Length check
    if len(response) > 50:
        score += 15.0
    if len(response) > 200:
        score += 10.0

    # Strategy-specific validation
    if strategy == "json_output":
        stripped = response.strip()
        if (
            (stripped.startswith("{") and stripped.endswith("}"))
            or (stripped.startswith("[") and stripped.endswith("]"))
        ):
            score += 25.0
        else:
            score -= 20.0
    elif strategy == "xml_output":
        if "<xml>" in response and "</xml>" in response:
            score += 25.0
        else:
            score -= 20.0
    elif strategy == "chain_of_thought":
        # Check if they actually thought step-by-step
        indicators = ["step", "first", "second", "therefore", "because", "then"]
        matches = sum(1 for ind in indicators if ind in response.lower())
        score += min(25.0, matches * 5.0)
    elif strategy == "role_prompt":
        # Check for formal tone indicators
        formal_terms = ["architecture", "standard", "optimal", "implement", "ensure"]
        matches = sum(1 for term in formal_terms if term in response.lower())
        score += min(15.0, matches * 3.0)
    else:
        score += 10.0  # Generic bump for completion

    return min(100.0, max(10.0, score))


def _calculate_consistency(response: str) -> float:
    """Calculate consistency score based on structure, style, and formatting."""
    score = 70.0
    # Check for paragraph structure
    paragraphs = [p for p in response.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        score += 10.0
    # Check for bullet points or lists
    if "-" in response or "*" in response or any(f"{i}." in response for i in range(10)):
        score += 10.0
    # Capitalization & grammar markers
    if response.strip() and response.strip()[0].isupper():
        score += 10.0
    return min(100.0, score)


async def execute_strategy(
    strategy: str, prompt: str, model: str
) -> PromptResult:
    """Execute a single prompt strategy and return results."""
    messages = []
    response_format = None

    if strategy == "zero_shot":
        messages = [{"role": "user", "content": prompt}]
    elif strategy == "few_shot":
        content = STRATEGY_TEMPLATES["few_shot"].format(prompt=prompt)
        messages = [{"role": "user", "content": content}]
    elif strategy == "chain_of_thought":
        content = STRATEGY_TEMPLATES["chain_of_thought"].format(prompt=prompt)
        messages = [{"role": "user", "content": content}]
    elif strategy == "role_prompt":
        tpl = STRATEGY_TEMPLATES["role_prompt"]
        messages = [
            {"role": "system", "content": tpl["system"]},
            {"role": "user", "content": tpl["user"].format(prompt=prompt)},
        ]
    elif strategy == "json_output":
        content = STRATEGY_TEMPLATES["json_output"].format(prompt=prompt)
        messages = [{"role": "user", "content": content}]
        response_format = {"type": "json_object"}
    elif strategy == "xml_output":
        content = STRATEGY_TEMPLATES["xml_output"].format(prompt=prompt)
        messages = [{"role": "user", "content": content}]
    elif strategy == "system_prompt":
        tpl = STRATEGY_TEMPLATES["system_prompt"]
        messages = [
            {"role": "system", "content": tpl["system"]},
            {"role": "user", "content": tpl["user"].format(prompt=prompt)},
        ]
    else:
        messages = [{"role": "user", "content": prompt}]

    result = await llm_service.chat_completion(
        messages=messages,
        model=model,
        response_format=response_format,
    )

    quality = _calculate_quality(result["response"], strategy)
    consistency = _calculate_consistency(result["response"])
    cost = llm_service.estimate_cost(
        model, result["input_tokens"], result["output_tokens"]
    )

    return PromptResult(
        strategy=strategy,
        response=result["response"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        total_tokens=result["total_tokens"],
        latency_ms=result["latency_ms"],
        cost_usd=cost,
        quality_score=quality,
        consistency_score=consistency,
    )


@router.post("/compare", response_model=PromptCompareResponse)
async def compare_strategies(
    request: PromptCompareRequest, db: AsyncSession = Depends(get_db)
):
    """Run one input prompt through all active engineering strategies concurrently."""
    trace_id = observability_service.generate_trace_id()
    tracer = observability_service.RequestTracer("prompt_lab", trace_id)

    tasks = [
        execute_strategy(strategy, request.prompt, request.model)
        for strategy in request.strategies
    ]

    tracer.start_step("strategies_execution", "llm_comparison")
    results = await asyncio.gather(*tasks)
    tracer.end_step(
        output_data={"strategies_tested": len(results)},
        metadata={"model": request.model},
    )

    # Log events to the DB for observability
    for r in results:
        await observability_service.log_request(
            db=db,
            trace_id=trace_id,
            module="prompt_lab",
            model=request.model,
            input_text=request.prompt,
            output_text=r.response,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            latency_ms=r.latency_ms,
            cost_usd=r.cost_usd,
            prompt_style=r.strategy,
            status="success",
        )

    return PromptCompareResponse(
        prompt=request.prompt,
        model=request.model,
        results=results,
        trace_id=trace_id,
    )


@router.post("/save-version")
async def save_version(
    name: str,
    prompt_text: str,
    system_prompt: str = None,
    style: str = "zero_shot",
    tags: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Save a specific prompt configuration to version history."""
    try:
        # Find latest version number
        q = select(PromptVersion).where(PromptVersion.name == name)
        res = await db.execute(q)
        existing = res.scalars().all()
        version = len(existing) + 1

        v = PromptVersion(
            name=name,
            prompt_text=prompt_text,
            system_prompt=system_prompt,
            version=version,
            style=style,
            tags=tags,
        )
        db.add(v)
        await db.commit()
        return {"status": "success", "version": version, "name": name}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions")
async def list_versions(db: AsyncSession = Depends(get_db)):
    """List all saved prompt versions."""
    try:
        q = select(PromptVersion).order_by(PromptVersion.created_at.desc())
        res = await db.execute(q)
        versions = res.scalars().all()
        return {
            "versions": [
                {
                    "id": v.id,
                    "name": v.name,
                    "prompt_text": v.prompt_text,
                    "system_prompt": v.system_prompt,
                    "version": v.version,
                    "style": v.style,
                    "tags": v.tags,
                    "created_at": v.created_at.isoformat(),
                }
                for v in versions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
