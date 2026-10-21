"""Runtime configuration, loaded from environment variables or a `.env` file."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LB_", extra="ignore")

    llm_provider: Literal["ollama", "gemini", "fake"] = "ollama"

    ollama_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b"
    ollama_vision_model: str = "qwen2.5vl:3b"
    ollama_embed_model: str = "nomic-embed-text"

    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "gemini-embedding-001"

    data_dir: Path = ROOT / "data"
    artifacts_dir: Path = ROOT / "artifacts"
    database_url: str = f"sqlite:///{(ROOT / 'artifacts' / 'liverbuddy.db').as_posix()}"

    jwt_secret: str = "dev-only-insecure-secret-change-me-in-production"
    jwt_ttl_minutes: int = 60 * 12

    api_url: str = "http://localhost:8000"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def index_dir(self) -> Path:
        return self.artifacts_dir / "index"

    @property
    def model_dir(self) -> Path:
        return self.artifacts_dir / "models"


@lru_cache
def get_settings() -> Settings:
    return Settings()
