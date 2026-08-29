from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class IntegrationProvider(StrEnum):
    N8N = "n8n"
    GEMINI = "gemini"
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CLOUDFLARE = "cloudflare"
    RENDER = "render"
    GITHUB = "github"
    SLACK = "slack"
    NOTION = "notion"
    GITLAB = "gitlab"
    MAKE = "make"


class IntegrationRequest(BaseModel):
    workflow: str = Field(min_length=1, max_length=200)
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)


class IntegrationResult(BaseModel):
    provider: IntegrationProvider
    workflow: str
    success: bool
    status_code: int | None = None
    data: Any = None
    error: str | None = None
    correlation_id: str | None = None


class IntegrationStatus(BaseModel):
    provider: IntegrationProvider
    name: str
    configured: bool
    requires: list[str] = Field(default_factory=list)
    connected: bool | None = None
    last_check: str | None = None
    last_check_latency_ms: float | None = None
    last_check_error: str | None = None
    last_execution: str | None = None
    last_execution_success: bool | None = None


# --- Unified connector catalog (Integration Hub) ---


class ConnectorType(StrEnum):
    MCP = "mcp"
    API = "api"
    OAUTH = "oauth"
    WEBHOOK = "webhook"


class ConnectorCategory(StrEnum):
    AUTOMATION = "automation"
    AI = "ai"
    DEVELOPER = "developer"
    PRODUCTIVITY = "productivity"
    GOOGLE = "google"
    DATA = "data"
    OTHER = "other"


class ConnectorAuthType(StrEnum):
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER = "bearer"
    WEBHOOK_SECRET = "webhook_secret"


class ConnectorStatusValue(StrEnum):
    CONNECTED = "connected"
    CONFIGURED = "configured"
    NEEDS_SETUP = "needs_setup"
    AVAILABLE = "available"
    ERROR = "error"
    DISABLED = "disabled"


class ConnectorEntry(BaseModel):
    """A catalog entry (static metadata) merged with its live computed status.

    `implemented=False` means this is catalog metadata only — there is no
    adapter behind it. Its status is always `available` ("not built yet"),
    never `needs_setup`/`configured`/`connected`, because those would imply
    working code that doesn't exist.
    """

    id: str
    name: str
    description: str
    category: ConnectorCategory
    connector_type: ConnectorType
    icon: str
    auth_type: ConnectorAuthType
    capabilities: list[str] = Field(default_factory=list)
    provider: str
    popular: bool = False
    documentation_url: str | None = None
    implemented: bool = False
    requires: list[str] = Field(default_factory=list)
    status: ConnectorStatusValue = ConnectorStatusValue.AVAILABLE
    configured: bool = False
    connected: bool | None = None
    last_check: str | None = None
    last_check_latency_ms: float | None = None
    last_check_error: str | None = None
    last_execution: str | None = None
    last_execution_success: bool | None = None
