from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from claim_assistant.web.services.processing import ClaimProcessingService
from claim_assistant.web.services.registry import ClaimFormsRegistry


def _default_project_dir() -> Path:
    """
    Resolve project root for runtime (expects repo layout: <root>/src/claim_assistant/web/...).

    If you deploy differently, override with env var:
      CLAIM_ASSISTANT_PROJECT_DIR=/abs/path/to/project/root
    """
    env = os.getenv("CLAIM_ASSISTANT_PROJECT_DIR")
    if env:
        return Path(env).expanduser().resolve()

    # .../src/claim_assistant/web/deps.py -> .../src/claim_assistant -> .../src -> <root>
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def get_logger() -> logging.Logger:
    """
    Single shared logger for API process.
    """
    logger = logging.getLogger("claim_assistant.api")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logger


@lru_cache(maxsize=1)
def get_project_dir() -> Path:
    return _default_project_dir()


@lru_cache(maxsize=1)
def get_registry() -> ClaimFormsRegistry:
    return ClaimFormsRegistry(project_dir=get_project_dir())


@lru_cache(maxsize=1)
def get_processing_service() -> ClaimProcessingService:
    return ClaimProcessingService(project_dir=get_project_dir())
