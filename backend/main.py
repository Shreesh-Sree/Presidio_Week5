"""AlgoQX Studio -- FastAPI Application Entry Point.

The Operating System for Enterprise AI.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import get_settings
from backend.database.engine import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan -- startup and shutdown events."""
    settings = get_settings()
    settings.ensure_directories()
    await init_db()
    yield


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="AlgoQX Studio",
        description="The Operating System for Enterprise AI",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS -- allow Streamlit frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    from backend.api.router import api_router
    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "AlgoQX Studio"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
