from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    app_name: str = "Joli"
    app_env: Literal["development", "production"] = "development"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./joli.db"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    chat_model: str = "deepseek/deepseek-chat-v3"
    document_model: str = "anthropic/claude-sonnet-4"

    max_upload_size_mb: int = 5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
