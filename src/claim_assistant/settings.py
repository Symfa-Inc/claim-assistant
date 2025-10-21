import os

from pydantic_settings import BaseSettings

from claim_assistant import PROJECT_DIR


class OpenAISettings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    openai_api_key: str

    class Config:
        env_file = os.path.join(PROJECT_DIR, "src", "claim_assistant", ".env")
        extra = "ignore"
