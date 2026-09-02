"""FastAPI dependency injection providers for persistence and core services."""
from __future__ import annotations

import os
from app.core.config import settings
from app.persistence.repository import Repository
from app.training.service import TrainingService

_repo_instance: Repository | None = None


def get_repo() -> Repository:
    global _repo_instance
    if _repo_instance is None:
        db_url = getattr(settings, "database_url", None) or os.getenv("DATABASE_URL") or os.getenv("DB_PATH", "data/app.db")
        _repo_instance = Repository(db_path=db_url)
    return _repo_instance


def get_training_service() -> TrainingService:
    repo = get_repo()
    return TrainingService(repo=repo)
