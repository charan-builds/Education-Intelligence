from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    ai_service_url: str = "http://ai_service:8100"
    ai_service_timeout_seconds: float = 10.0
    recommendation_engine: str = "rule"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    default_tenant_id: int = 1
    outbox_max_attempts: int = 5
    outbox_retry_delay_seconds: int = 60
    outbox_cleanup_days: int = 7
    outbox_processing_timeout_seconds: int = 900
    audit_log_file_path: str | None = None
    audit_max_lookback_days: int = 30
    audit_log_max_bytes: int = 10_485_760
    audit_log_backup_count: int = 5
    audit_log_read_max_lines: int = 50_000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
