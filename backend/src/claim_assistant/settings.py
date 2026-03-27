import os

from claim_assistant import PROJECT_DIR
from pydantic_settings import BaseSettings


class OpenAISettings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    openai_api_key: str

    class Config:
        env_file = os.path.join(PROJECT_DIR, "src", "claim_assistant", ".env")
        extra = "ignore"


class AzureDocumentIntelligenceSettings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    documentintelligence_endpoint: str
    documentintelligence_api_key: str

    class Config:
        env_file = os.path.join(PROJECT_DIR, "src", "claim_assistant", ".env")
        extra = "ignore"
