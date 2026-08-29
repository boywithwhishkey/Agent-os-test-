from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "THYNACT"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    api_key: str | None = Field(default=None, validation_alias="AGENT_OS_API_KEY")
    cors_origins: str = Field(
        default=(
            "http://localhost:3000,http://localhost:5173,"
            "http://127.0.0.1:5000,https://agent-os-test.pages.dev,"
            "https://app.thynact.com"
        ),
        validation_alias="AGENT_OS_CORS_ORIGINS",
    )
    llm_provider: str = Field(default="mock", validation_alias="AGENT_OS_LLM_PROVIDER")
    llm_model: str = Field(
        default="gemini-3.1-flash-lite",
        validation_alias="AGENT_OS_LLM_MODEL",
    )
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    cloudflare_api_token: str | None = Field(default=None, validation_alias="CLOUDFLARE_API_TOKEN")
    render_api_key: str | None = Field(default=None, validation_alias="RENDER_API_KEY")
    github_oauth_client_id: str | None = Field(default=None, validation_alias="GITHUB_OAUTH_CLIENT_ID")
    github_oauth_client_secret: str | None = Field(
        default=None, validation_alias="GITHUB_OAUTH_CLIENT_SECRET"
    )
    slack_oauth_client_id: str | None = Field(default=None, validation_alias="SLACK_OAUTH_CLIENT_ID")
    slack_oauth_client_secret: str | None = Field(
        default=None, validation_alias="SLACK_OAUTH_CLIENT_SECRET"
    )
    notion_oauth_client_id: str | None = Field(default=None, validation_alias="NOTION_OAUTH_CLIENT_ID")
    notion_oauth_client_secret: str | None = Field(
        default=None, validation_alias="NOTION_OAUTH_CLIENT_SECRET"
    )
    gitlab_oauth_client_id: str | None = Field(default=None, validation_alias="GITLAB_OAUTH_CLIENT_ID")
    gitlab_oauth_client_secret: str | None = Field(
        default=None, validation_alias="GITLAB_OAUTH_CLIENT_SECRET"
    )
    make_webhook_url: str | None = Field(default=None, validation_alias="MAKE_WEBHOOK_URL")
    make_webhook_auth_header: str | None = Field(
        default=None, validation_alias="MAKE_WEBHOOK_AUTH_HEADER"
    )
    make_webhook_auth_value: str | None = Field(
        default=None, validation_alias="MAKE_WEBHOOK_AUTH_VALUE"
    )
    oauth_redirect_base_url: str = Field(
        default="https://api.thynact.com", validation_alias="AGENT_OS_OAUTH_REDIRECT_BASE_URL"
    )
    frontend_base_url: str = Field(
        default="https://app.thynact.com", validation_alias="AGENT_OS_FRONTEND_URL"
    )
    max_parallel: int = Field(default=3, ge=1, validation_alias="AGENT_OS_MAX_PARALLEL")
    max_retries: int = Field(default=2, ge=0, validation_alias="AGENT_OS_MAX_RETRIES")
    max_jobs: int = Field(default=6, ge=1, validation_alias="AGENT_OS_MAX_JOBS")
    autonomous_timeout_seconds: float = Field(
        default=120.0, gt=0, validation_alias="AGENT_OS_AUTONOMOUS_TIMEOUT_SECONDS"
    )
    n8n_base_url: str = Field(default="", validation_alias="N8N_BASE_URL")
    n8n_webhook_prefix: str = Field(default="webhook", validation_alias="N8N_WEBHOOK_PREFIX")
    n8n_auth_header: str | None = Field(
        default=None, validation_alias="N8N_WEBHOOK_AUTH_HEADER"
    )
    n8n_auth_value: str | None = Field(
        default=None, validation_alias="N8N_WEBHOOK_AUTH_VALUE"
    )
    circuit_failures: int = Field(
        default=3, ge=1, validation_alias="AGENT_OS_CIRCUIT_FAILURES"
    )
    circuit_recovery_seconds: float = Field(
        default=30.0, gt=0, validation_alias="AGENT_OS_CIRCUIT_RECOVERY_SECONDS"
    )
    integration_rate_limit: int = Field(
        default=60, ge=1, validation_alias="AGENT_OS_INTEGRATION_RATE_LIMIT"
    )
    integration_rate_window: float = Field(
        default=60.0, gt=0, validation_alias="AGENT_OS_INTEGRATION_RATE_WINDOW"
    )
    retry_backoff_base: float = Field(
        default=0.25, ge=0, validation_alias="AGENT_OS_RETRY_BACKOFF_BASE"
    )
    memory_backend: str = Field(default="memory", validation_alias="AGENT_OS_MEMORY_BACKEND")
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    db_pool_min: int = Field(default=1, ge=1, validation_alias="AGENT_OS_DB_POOL_MIN")
    db_pool_max: int = Field(default=10, ge=1, validation_alias="AGENT_OS_DB_POOL_MAX")
    db_command_timeout: float = Field(
        default=30.0, gt=0, validation_alias="AGENT_OS_DB_COMMAND_TIMEOUT"
    )
    queue_backend: str = Field(default="memory", validation_alias="AGENT_OS_QUEUE_BACKEND")
    queue_prefix: str = Field(default="agent-os", validation_alias="AGENT_OS_QUEUE_PREFIX")
    redis_url: str = Field(default="", validation_alias="REDIS_URL")
    workflow_backend: str = Field(default="memory", validation_alias="AGENT_OS_WORKFLOW_BACKEND")
    runtime_backend: str = Field(default="memory", validation_alias="AGENT_OS_RUNTIME_BACKEND")
    task_backend: str = Field(default="memory", validation_alias="AGENT_OS_TASK_BACKEND")
    tool_backend: str = Field(default="memory", validation_alias="AGENT_OS_TOOL_BACKEND")
    workflow_definition_backend: str = Field(
        default="memory", validation_alias="AGENT_OS_WORKFLOW_DEFINITION_BACKEND"
    )
    embedding_backend: str = Field(
        default="deterministic", validation_alias="AGENT_OS_EMBEDDING_BACKEND"
    )
    embedding_dimensions: int = Field(
        default=64, ge=1, validation_alias="AGENT_OS_EMBEDDING_DIMENSIONS"
    )
    semantic_weight: float = Field(
        default=0.75, ge=0, validation_alias="AGENT_OS_SEMANTIC_WEIGHT"
    )
    lexical_weight: float = Field(
        default=0.25, ge=0, validation_alias="AGENT_OS_LEXICAL_WEIGHT"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def get_settings() -> Settings:
    """Load the current environment through the typed settings model."""
    return Settings()
