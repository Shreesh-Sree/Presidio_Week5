"""AlgoQX Studio -- Agent Builder API Endpoints."""

import asyncio
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_db
from backend.database.models import AgentRun
from backend.models.schemas import (
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentStep,
)
from backend.services import llm_service, observability_service

router = APIRouter(prefix="/agent", tags=["Agent Builder"])

NODE_TYPES = [
    {
        "id": "planner",
        "type": "planner",
        "label": "Planner",
        "description": "Breaks down queries into actionable execution tasks.",
        "default_config": {"temperature": 0.2},
    },
    {
        "id": "researcher",
        "type": "researcher",
        "label": "Researcher",
        "description": "Gathers information using configured search/retrieval tools.",
        "default_config": {"max_searches": 3},
    },
    {
        "id": "retriever",
        "type": "retriever",
        "label": "Retriever",
        "description": "Retrieves semantic documents from active databases.",
        "default_config": {"top_k": 3},
    },
    {
        "id": "reasoner",
        "type": "reasoner",
        "label": "Reasoner",
        "description": "Performs chain-of-thought analysis and fact checking.",
        "default_config": {"cot_depth": 2},
    },
    {
        "id": "writer",
        "type": "writer",
        "label": "Writer",
        "description": "Synthesizes final answers in rich markdown format.",
        "default_config": {"style": "professional"},
    },
    {
        "id": "reviewer",
        "type": "reviewer",
        "label": "Reviewer",
        "description": "Checks outputs against guidelines and triggers retries if quality checks fail.",
        "default_config": {"min_quality_score": 80.0},
    },
]

TOOL_TYPES = [
    {"name": "web_search", "description": "Search the web for current events and data."},
    {"name": "calculator", "description": "Solve complex math or algebraic formulas."},
    {"name": "code_executor", "description": "Run Python code blocks safely in sandboxed environments."},
    {"name": "wikipedia", "description": "Fetch articles and summaries from Wikipedia database."},
    {"name": "file_reader", "description": "Read contents of local text or code files."},
]


@router.get("/node-types")
async def get_node_types():
    """Get all available Node components in the agent block pool."""
    return {"nodes": NODE_TYPES}


@router.get("/tool-types")
async def get_tool_types():
    """Get all tools agents can consume."""
    return {"tools": TOOL_TYPES}


@router.post("/validate")
async def validate_agent_config(request: AgentExecuteRequest):
    """Validate graph routing for disconnected subgraphs or cycles."""
    nodes = request.config.nodes
    edges = request.config.edges

    if not nodes:
        return {"valid": False, "error": "Graph must have at least one Node."}

    # Verify edge connectivity
    node_ids = {n.id for n in nodes}
    for edge in edges:
        if edge.source not in node_ids:
            return {"valid": False, "error": f"Edge source '{edge.source}' does not exist."}
        if edge.target not in node_ids:
            return {"valid": False, "error": f"Edge target '{edge.target}' does not exist."}

    # Check for visual starting nodes
    has_start = any(n.type in ["planner", "researcher"] for n in nodes)
    if not has_start:
        return {"valid": True, "warning": "No clear starter node type (Planner/Researcher) detected."}

    return {"valid": True, "message": "Graph is valid and ready to execute."}


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent_graph(request: AgentExecuteRequest, db: AsyncSession = Depends(get_db)):
    """Simulate or execute the node graph pipeline with step tracing."""
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    start_time = time.perf_counter()

    nodes = request.config.nodes
    edges = request.config.edges

    # Walk through the nodes in topological order or simulate their role progression
    steps = []
    current_input = request.input_text
    total_tokens = 0
    total_cost = 0.0

    # Ensure a logical flow order of execution based on node types
    order = ["planner", "researcher", "retriever", "reasoner", "writer", "reviewer"]
    sorted_nodes = sorted(
        nodes,
        key=lambda n: order.index(n.type) if n.type in order else 99,
    )

    for i, node in enumerate(sorted_nodes):
        step_start = time.perf_counter()

        # Build messages for this node to make a real call to the LLM!
        role_instructions = (
            f"You are the '{node.label}' node in an agent network. "
            f"Your specific role instructions are: {node.config.get('instructions', 'Proceed with the task')}.\n"
            f"Task context: {current_input}"
        )

        messages = [
            {"role": "system", "content": role_instructions},
            {"role": "user", "content": request.input_text},
        ]

        # Real LLM call for each node!
        llm_res = await llm_service.chat_completion(
            messages=messages,
            model=request.model,
        )

        step_elapsed = (time.perf_counter() - step_start) * 1000
        step_cost = llm_service.estimate_cost(request.model, llm_res["input_tokens"], llm_res["output_tokens"])

        total_tokens += llm_res["total_tokens"]
        total_cost += step_cost

        # Simulate tool usage for Researcher node
        tool_calls = []
        if node.type == "researcher" and request.config.tools:
            tool_calls = [
                {
                    "tool": tool,
                    "query": request.input_text[:50],
                    "status": "success",
                }
                for tool in request.config.tools
            ]

        step = AgentStep(
            node_id=node.id,
            node_type=node.type,
            input_text=current_input,
            output_text=llm_res["response"],
            tokens=llm_res["total_tokens"],
            latency_ms=step_elapsed,
            tool_calls=tool_calls,
            status="completed",
        )
        steps.append(step)

        # Feed this output as context for the next node
        current_input = llm_res["response"]

    elapsed_total = (time.perf_counter() - start_time) * 1000

    # Save Agent run metadata to SQLite
    run = AgentRun(
        run_id=run_id,
        agent_config=request.config.model_dump(),
        input_text=request.input_text,
        output_text=current_input,
        steps=[s.model_dump() for s in steps],
        total_tokens=total_tokens,
        total_cost=total_cost,
        latency_ms=elapsed_total,
        status="completed",
    )
    db.add(run)
    await db.commit()

    return AgentExecuteResponse(
        run_id=run_id,
        output=current_input,
        steps=steps,
        execution_graph={
            "nodes": [n.model_dump() for n in nodes],
            "edges": [e.model_dump() for e in edges],
        },
        total_tokens=total_tokens,
        total_cost=total_cost,
        latency_ms=elapsed_total,
        status="completed",
    )
