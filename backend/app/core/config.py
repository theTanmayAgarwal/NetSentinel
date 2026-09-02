"""Application configuration.

Deliberately dependency-free (standard library only) so the core engine and its
tests can run in any environment — including an offline sandbox — without needing
pydantic or a web framework installed. The FastAPI layer imports this too.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR: Path = Path(__file__).resolve().parents[2]
REPO_ROOT: Path = BACKEND_DIR.parent
DATA_DIR: Path = REPO_ROOT / "data"
SAMPLE_CONFIGS_DIR: Path = REPO_ROOT / "sample_configs"

try:
    import dotenv
    # Find .env in REPO_ROOT or BACKEND_DIR
    for env_path in [REPO_ROOT / ".env", BACKEND_DIR / ".env"]:
        if env_path.exists():
            dotenv.load_dotenv(env_path, override=True)
            break
except ImportError:
    pass



def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    """Runtime settings, sourced from environment variables with safe defaults."""

    app_name: str = os.getenv(
        "APP_NAME", "AI-Driven Multi-Vendor Network Security Compliance Auditor"
    )
    app_env: str = os.getenv("APP_ENV", "development")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        )
    )
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "auto")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.80"))
    version: str = "0.1.0"


settings = Settings()
