from app.integrations.base import IntegrationAdapter


class ConnectorRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, IntegrationAdapter] = {}

    def register(self, name: str, adapter: IntegrationAdapter) -> None:
        key = name.lower().strip()
        if not key:
            raise ValueError("Connector name is required")
        self._adapters[key] = adapter

    def get(self, name: str) -> IntegrationAdapter:
        try:
            return self._adapters[name.lower().strip()]
        except KeyError as exc:
            raise KeyError(f"Unknown connector: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._adapters)
