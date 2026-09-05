from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "THYNACT"
    app_env: str = Field(default="development", validation_alias="AGENT_OS_APP_ENV")
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
    discord_webhook_url: str | None = Field(default=None, validation_alias="DISCORD_WEBHOOK_URL")
    telegram_bot_token: str | None = Field(default=None, validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_default_chat_id: str | None = Field(
        default=None, validation_alias="TELEGRAM_DEFAULT_CHAT_ID"
    )
    meta_access_token: str | None = Field(default=None, validation_alias="META_ACCESS_TOKEN")
    meta_graph_api_version: str = Field(default="v23.0", validation_alias="META_GRAPH_API_VERSION")
    whatsapp_phone_number_id: str | None = Field(
        default=None, validation_alias="WHATSAPP_PHONE_NUMBER_ID"
    )
    instagram_business_account_id: str | None = Field(
        default=None, validation_alias="INSTAGRAM_BUSINESS_ACCOUNT_ID"
    )
    teams_webhook_url: str | None = Field(default=None, validation_alias="TEAMS_WEBHOOK_URL")
    shopify_admin_access_token: str | None = Field(
        default=None, validation_alias="SHOPIFY_ADMIN_ACCESS_TOKEN"
    )
    shopify_shop_domain: str | None = Field(default=None, validation_alias="SHOPIFY_SHOP_DOMAIN")
    shopify_api_version: str = Field(default="2025-07", validation_alias="SHOPIFY_API_VERSION")
    stripe_secret_key: str | None = Field(default=None, validation_alias="STRIPE_SECRET_KEY")
    snapchat_access_token: str | None = Field(default=None, validation_alias="SNAPCHAT_ACCESS_TOKEN")
    woocommerce_store_url: str | None = Field(default=None, validation_alias="WOOCOMMERCE_STORE_URL")
    woocommerce_consumer_key: str | None = Field(
        default=None, validation_alias="WOOCOMMERCE_CONSUMER_KEY"
    )
    woocommerce_consumer_secret: str | None = Field(
        default=None, validation_alias="WOOCOMMERCE_CONSUMER_SECRET"
    )
    vercel_api_token: str | None = Field(default=None, validation_alias="VERCEL_API_TOKEN")
    vercel_team_id: str | None = Field(default=None, validation_alias="VERCEL_TEAM_ID")
    linear_api_key: str | None = Field(default=None, validation_alias="LINEAR_API_KEY")
    amazon_lwa_client_id: str | None = Field(
        default=None, validation_alias="AMAZON_LWA_CLIENT_ID"
    )
    amazon_lwa_client_secret: str | None = Field(
        default=None, validation_alias="AMAZON_LWA_CLIENT_SECRET"
    )
    amazon_lwa_refresh_token: str | None = Field(
        default=None, validation_alias="AMAZON_LWA_REFRESH_TOKEN"
    )
    amazon_aws_access_key_id: str | None = Field(
        default=None, validation_alias="AMAZON_AWS_ACCESS_KEY_ID"
    )
    amazon_aws_secret_access_key: str | None = Field(
        default=None, validation_alias="AMAZON_AWS_SECRET_ACCESS_KEY"
    )
    amazon_aws_session_token: str | None = Field(
        default=None, validation_alias="AMAZON_AWS_SESSION_TOKEN"
    )
    amazon_region: str = Field(default="na", validation_alias="AMAZON_REGION")
    google_oauth_client_id: str | None = Field(
        default=None, validation_alias="GOOGLE_OAUTH_CLIENT_ID"
    )
    google_oauth_client_secret: str | None = Field(
        default=None, validation_alias="GOOGLE_OAUTH_CLIENT_SECRET"
    )
    jira_oauth_client_id: str | None = Field(
        default=None, validation_alias="JIRA_OAUTH_CLIENT_ID"
    )
    jira_oauth_client_secret: str | None = Field(
        default=None, validation_alias="JIRA_OAUTH_CLIENT_SECRET"
    )
    jira_cloud_id: str | None = Field(default=None, validation_alias="JIRA_CLOUD_ID")
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

    # Interactive API docs. Public by default (useful in dev/staging); the
    # property below turns them off in production unless deliberately enabled,
    # so the full route surface is not published to anonymous callers.
    enable_docs: bool | None = Field(default=None, validation_alias="AGENT_OS_ENABLE_DOCS")

    require_durable_persistence: bool = Field(
        default=False, validation_alias="AGENT_OS_REQUIRE_DURABLE_PERSISTENCE"
    )

    @field_validator("app_env")
    @classmethod
    def _validate_app_env(cls, value: str) -> str:
        """Reject unknown environment names.

        AGENT_OS_APP_ENV is load-bearing: it decides the Redis namespace and is
        checked against the database's environment stamp. A typo like "prod"
        would silently create a THIRD environment sharing nothing with either
        real one, so fail on an unknown value rather than inventing it.
        """
        normalized = value.strip().lower()
        allowed = {"production", "staging", "development", "test"}
        if normalized not in allowed:
            raise ValueError(
                f"AGENT_OS_APP_ENV must be one of {sorted(allowed)}, got {value!r}"
            )
        return normalized

    @property
    def docs_enabled(self) -> bool:
        if self.enable_docs is not None:
            return self.enable_docs
        return self.app_env != "production"

    @property
    def is_production_like(self) -> bool:
        """Environments where losing state on restart is not acceptable."""
        return self.app_env in {"production", "staging"}

    @property
    def ephemeral_subsystems(self) -> list[str]:
        """Subsystems currently backed by process memory, so lost on restart."""
        backends = {
            "memory": self.memory_backend,
            "task": self.task_backend,
            "workflow": self.workflow_backend,
            "workflow_definition": self.workflow_definition_backend,
            "runtime": self.runtime_backend,
            "tool": self.tool_backend,
            "queue": self.queue_backend,
        }
        return sorted(name for name, backend in backends.items() if backend == "memory")

    @property
    def persistence_mode(self) -> str:
        ephemeral = self.ephemeral_subsystems
        if not ephemeral:
            return "durable"
        if len(ephemeral) == 7:
            return "ephemeral"
        return "partial"

    def persistence_warnings(self) -> list[str]:
        """Configuration problems that would otherwise degrade silently."""
        warnings: list[str] = []
        ephemeral = self.ephemeral_subsystems
        if self.is_production_like and ephemeral:
            warnings.append(
                f"{self.app_env} is running with in-memory backends "
                f"({', '.join(ephemeral)}); this state is lost on every restart"
            )
        # Every postgres-selecting backend, not just memory_backend. Checking
        # one of six meant a cutover that set AGENT_OS_TASK_BACKEND=postgres and
        # forgot DATABASE_URL reported NO warning, then failed at request time
        # with an opaque "DATABASE_URL is required" from deep inside a store
        # factory. Naming the offenders makes the fix obvious.
        if not self.database_url:
            needs_database = sorted(
                name
                for name, backend in {
                    "memory": self.memory_backend,
                    "task": self.task_backend,
                    "workflow": self.workflow_backend,
                    "workflow_definition": self.workflow_definition_backend,
                    "runtime": self.runtime_backend,
                    "tool": self.tool_backend,
                }.items()
                if backend in {"postgres", "postgres_pgvector"}
            )
            if needs_database:
                warnings.append(
                    "a postgres backend is selected for "
                    f"{', '.join(needs_database)} but DATABASE_URL is empty"
                )
        if self.queue_backend == "redis" and not self.redis_url:
            warnings.append("the redis queue backend is selected but REDIS_URL is empty")
        return warnings

    @property
    def queue_namespace(self) -> str:
        """Redis key prefix, namespaced per environment.

        Production and staging should have separate Redis instances, but if they
        ever do share one, unprefixed keys would let staging consume production
        jobs. Namespacing makes that collision impossible rather than unlikely.
        """
        return f"{self.queue_prefix}:{self.app_env}"

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
