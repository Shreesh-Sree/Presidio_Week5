"""AlgoQX Studio -- Model Context Protocol API Endpoints."""

import time
from fastapi import APIRouter, HTTPException
import httpx

from backend.models.schemas import MCPCallRequest, MCPCallResponse

router = APIRouter(prefix="/mcp", tags=["MCP"])


@router.get("/info")
async def get_mcp_info():
    """Get conceptual description of Model Context Protocol (MCP)."""
    return {
        "title": "Model Context Protocol (MCP)",
        "description": "Introduced by Anthropic, MCP is an open standard that acts as a 'universal connector' for AI models. Instead of writing custom API wrappers for every database, web service, or file system, a client exposes standard capabilities (Tools, Resources, Prompts) that LLMs can consume via JSON-RPC 2.0.",
        "primitives": [
            {
                "name": "Tools",
                "description": "Executable actions the model can trigger (e.g., query database, create files, write code). Similar to OpenAI Function Calling but standardized.",
            },
            {
                "name": "Resources",
                "description": "URI-addressable read-only data sources (e.g., file contents, database rows, live logging streams). Allows models to fetch context programmatically.",
            },
            {
                "name": "Prompts",
                "description": "Predefined prompt templates exposed by the server. Helpful for steering models in standardized workflows.",
            },
        ],
    }


@router.get("/servers")
async def get_mcp_servers():
    """List supported server connectors."""
    return {
        "servers": [
            {
                "name": "Filesystem",
                "description": "Allows the LLM to inspect, read, and write files safely within designated project workspace directories.",
                "status": "available",
            },
            {
                "name": "GitHub",
                "description": "Provides capabilities to search code repositories, list branches, inspect issues, and create Pull Requests.",
                "status": "available",
            },
            {
                "name": "SQLite",
                "description": "Allows executing read/write SQL commands, listing tables, and inspecting schema structures.",
                "status": "available",
            },
            {
                "name": "Browser",
                "description": "Exposes automated browser sessions to fetch webpage DOM structure, capture screenshots, and scrape content.",
                "status": "available",
            },
        ]
    }


@router.post("/demo/rest")
async def demo_rest_call(url: str = "https://jsonplaceholder.typicode.com/posts/1"):
    """Make a REST API call to a user-provided URL."""
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=10.0)
            data = res.json()
        elapsed = (time.perf_counter() - start) * 1000
        return {
            "endpoint": url,
            "method": "GET",
            "latency_ms": round(elapsed, 2),
            "response": data,
            "explanation": "REST API requires a fixed endpoint structure, manual integration, and tight coupling of route names in client code.",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch REST endpoint: {str(e)}"
        )


@router.post("/demo/mcp", response_model=MCPCallResponse)
async def demo_mcp_call(request: MCPCallRequest):
    """Execute an MCP Tool Call with user-provided parameters."""
    start = time.perf_counter()
    try:
        tool_name = request.tool_name
        args = request.arguments
        server = request.server_type

        # Execute MCP tool with user input
        # Note: Real MCP integration would connect to actual MCP servers
        result = {
            "message": f"Executed MCP tool '{tool_name}' on '{server}' server with arguments: {args}",
            "tool_name": tool_name,
            "server": server,
            "arguments": args,
            "note": "This is a demonstration. Real MCP servers would execute actual tools."
        }

        elapsed = (time.perf_counter() - start) * 1000
        return MCPCallResponse(
            tool_name=tool_name,
            result=result,
            latency_ms=round(elapsed, 2),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison")
async def get_comparison():
    """Return comparison matrix between MCP and REST."""
    return {
        "comparison": [
            {
                "feature": "Architecture",
                "rest": "Tight Coupling (specific endpoints per action)",
                "mcp": "Loose Coupling (universal client consumes standardized servers)",
            },
            {
                "feature": "Discovery",
                "rest": "Manual Swagger/OpenAPI routing, code regeneration",
                "mcp": "Dynamic Tool Discovery (list_tools() called at initialization)",
            },
            {
                "feature": "State/Session",
                "rest": "Stateless, auth headers on every call",
                "mcp": "Stateful JSON-RPC connection over Stdio/SSE transport",
            },
            {
                "feature": "Schema",
                "rest": "Proprietary, custom Pydantic schemas",
                "mcp": "Standardized JSON schemas for parameters & output text",
            },
            {
                "feature": "Real-time updates",
                "rest": "WebSockets/SSE setup manually",
                "mcp": "Native support for streamed token outputs & logs",
            },
        ]
    }


@router.get("/architecture")
async def get_architecture():
    """Return MCP component diagrams data."""
    return {
        "diagram": (
            "Host App (AlgoQX Studio)\n"
            "       |\n"
            "   [JSON-RPC 2.0]\n"
            "       |\n"
            "   MCP Client Session\n"
            "       |\n"
            "   [Transport: Stdio / SSE]\n"
            "       |\n"
            "   MCP Server (Filesystem, SQLite, GitHub, Browser)\n"
        )
    }
