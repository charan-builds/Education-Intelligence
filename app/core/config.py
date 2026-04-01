from functools import lru_cache
from uuid import uuid4

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://localhost:6379"
    rate_limit_storage_url: str | None = None
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"
    ai_service_url: str = "http://ai_service:8100"
    ai_service_timeout_seconds: float = 10.0
    recommendation_engine: str = "rule"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    secret_key: str = Field(validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 20160
    invite_token_expire_hours: int = 72
    auth_cookie_secure: bool = True
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: str | None = None
    database_pool_size: int = 20
    database_max_overflow: int = 40
    database_pool_timeout_seconds: int = 30
    database_pool_recycle_seconds: int = 1800
    database_pool_use_lifo: bool = True
    environment: str = "development"
    default_tenant_id: int = 1
    outbox_max_attempts: int = 5
    outbox_retry_delay_seconds: int = 60
    outbox_cleanup_days: int = 7
    outbox_processing_timeout_seconds: int = 900
    outbox_retry_base_delay_seconds: int = 30
    outbox_dead_letter_retention_days: int = 14
    realtime_instance_id: str = uuid4().hex
    realtime_pubsub_channel_prefix: str = "realtime"
    realtime_presence_ttl_seconds: int = 60
    realtime_presence_sync_interval_seconds: int = 15
    db_slow_query_threshold_ms: int = 250
    tracing_enabled: bool = True
    tracing_service_name: str = "learning-platform-api"
    tracing_exporter_otlp_endpoint: str | None = None
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout_seconds: int = 30
    precomputed_analytics_ttl_seconds: int = 300
    search_backend: str = "db"
    search_url: str | None = None
    search_api_key: str | None = None
    search_index_prefix: str = "learning_platform"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    s3_region: str = "us-east-1"
    cdn_base_url: str | None = None
    upload_max_bytes: int = 25_000_000
    upload_allowed_content_types: str = (
        "application/pdf,image/png,image/jpeg,image/webp,text/plain,text/markdown,"
        "application/json,video/mp4"
    )
    upload_metadata_max_keys: int = 24
    upload_metadata_max_value_length: int = 500
    s3_presign_expiry_seconds: int = 900
    app_base_url: str = "http://localhost:3000"
    email_enabled: bool = False
    email_provider: str = "log"
    email_from_address: str = "no-reply@example.com"
    email_from_name: str = "Learning Intelligence Platform"
    email_reply_to: str | None = None
    email_sendgrid_api_key: str | None = None
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_smtp_username: str | None = None
    email_smtp_password: str | None = None
    email_smtp_use_tls: bool = True
    email_smtp_use_ssl: bool = False
    email_template_logo_url: str | None = None
    sentry_dsn: str | None = None
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    backup_s3_prefix: str = "db-backups"
    audit_log_file_path: str | None = None
    audit_max_lookback_days: int = 30
    audit_log_max_bytes: int = 10_485_760
    audit_log_backup_count: int = 5
    audit_log_read_max_lines: int = 50_000
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_client_id: str = "learning-platform-api"
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str | None = None
    kafka_sasl_username: str | None = None
    kafka_sasl_password: str | None = None
    kafka_topic_learning_events: str = "learning_events.v1"
    kafka_topic_notifications: str = "notifications.v1"
    kafka_topic_analytics: str = "analytics.v1"
    kafka_consumer_group_prefix: str = "learning-platform"
    kafka_consumer_poll_timeout_ms: int = 1000
    kafka_consumer_batch_size: int = 100
    kafka_replay_consumer_group_suffix: str = "replay"
    search_timeout_seconds: float = 3.0
    meilisearch_index_name: str = "learning-platform-content"
    elasticsearch_index_name: str = "learning-platform-content"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    @model_validator(mode="after")
    def validate_security_posture(self) -> "Settings":
        environment = self.environment.strip().lower()
        normalized_secret = self.secret_key.strip().lower()
        insecure_markers = {
            "changeme",
            "change-me",
            "replace-me",
            "replace-with-a-long-random-secret",
            "supersecret",
            "supersecretkey",
            "dev-secret",
        }

        if environment == "production":
            if len(self.secret_key.strip()) < 32 or any(marker in normalized_secret for marker in insecure_markers):
                raise ValueError("JWT_SECRET/SECRET_KEY must be a strong production secret")
            if not self.auth_cookie_secure:
                raise ValueError("AUTH_COOKIE_SECURE must be true in production")
            if not self.app_base_url.startswith("https://"):
                raise ValueError("APP_BASE_URL must use https in production")

        provider = self.email_provider.strip().lower()
        if provider not in {"log", "sendgrid", "smtp"}:
            raise ValueError("EMAIL_PROVIDER must be one of: log, sendgrid, smtp")
        if provider == "sendgrid" and self.email_enabled and not self.email_sendgrid_api_key:
            raise ValueError("EMAIL_SENDGRID_API_KEY is required when EMAIL_PROVIDER=sendgrid and email is enabled")
        if provider == "smtp" and self.email_enabled and not self.email_smtp_host:
            raise ValueError("EMAIL_SMTP_HOST is required when EMAIL_PROVIDER=smtp and email is enabled")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
