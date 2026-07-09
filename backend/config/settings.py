"""AlgoQX Studio -- Configuration Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # -- LLM --
    llm_base_url: str = "https://ollama.algoqx.tech/v1"
    llm_api_key: str = "sk-ollama-algoqx-2024"
    llm_default_model: str = "qwen2.5-7b-instruct:latest"

    # -- Database --
    database_url: str = "sqlite+aiosqlite:///./data/algoqx.db"

    # -- Embeddings --
    embedding_model: str = "qwen3-embedding:8b"
    embedding_fallback_model: str = "test-qwen-fast:latest"

    # -- FAISS --
    faiss_index_path: str = "./data/faiss_index"

    # -- Server --
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 8501

    # -- Security --
    secret_key: str = "algoqx-studio-secret-change-in-production"

    # -- Paths --
    upload_dir: str = "./data/uploads"
    db_dir: str = "./data"

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    def ensure_directories(self) -> None:
        """Create required data directories if they don't exist."""
        for dir_path in [self.upload_dir, self.faiss_index_path, self.db_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    settings = Settings()
    settings.ensure_directories()
    return settings
