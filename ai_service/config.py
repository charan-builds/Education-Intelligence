from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 15.0

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-5-mini"
    openai_timeout_seconds: float = 20.0

    fallback_api_key: str | None = None
    fallback_base_url: str | None = None
    fallback_model: str = "gpt-4o-mini"
    fallback_timeout_seconds: float = 20.0

    openai_max_retries: int = 3
    ai_cache_ttl_seconds: int = 900
    ai_request_max_input_chars: int = 4000
    ai_chat_history_limit: int = 6
    ai_service_log_prompts: bool = False
    ai_temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_model_names(self) -> "AISettings":
        if self.openai_model.strip() == "gpt-5.4-mini":
            self.openai_model = "gpt-5-mini"
        return self


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()
