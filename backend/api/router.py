"""AlgoQX Studio -- Main API Router."""

from fastapi import APIRouter

from backend.api.llm_explorer import router as llm_router
from backend.api.prompt_lab import router as prompt_router
from backend.api.rag_studio import router as rag_router
from backend.api.agent_builder import router as agent_router
from backend.api.mcp import router as mcp_router
from backend.api.app_builder import router as app_router
from backend.api.security import router as security_router
from backend.api.privacy import router as privacy_router
from backend.api.observability import router as observability_router
from backend.api.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(llm_router)
api_router.include_router(prompt_router)
api_router.include_router(rag_router)
api_router.include_router(agent_router)
api_router.include_router(mcp_router)
api_router.include_router(app_router)
api_router.include_router(security_router)
api_router.include_router(privacy_router)
api_router.include_router(observability_router)
api_router.include_router(analytics_router)
