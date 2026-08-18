from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.tools.models import ToolRisk
from app.tools.registry import RegisteredTool, ToolRegistry

SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
}
MAX_READ_BYTES = 1_000_000
MAX_ARTIFACT_BYTES = 2_000_000


def get_workspace_root() -> Path:
    return Path(os.getenv("AGENT_OS_WORKSPACE_ROOT", Path.cwd())).resolve()


def get_artifact_root() -> Path:
    raw = os.getenv("AGENT_OS_ARTIFACT_ROOT")
    if raw:
        return Path(raw).resolve()
    return (get_workspace_root() / "artifacts").resolve()


def _safe_workspace_path(value: str) -> Path:
    root = get_workspace_root()
    path = (root / value).resolve()
    if path != root and root not in path.parents:
        raise ValueError("Path escapes the workspace")
    return path


def _reject_sensitive(path: Path) -> None:
    if path.name in SENSITIVE_NAMES:
        raise PermissionError("Reading sensitive credential files is blocked")
    lowered = {part.lower() for part in path.parts}
    if ".git" in lowered or ".ssh" in lowered:
        raise PermissionError("Reading protected repository/SSH metadata is blocked")


async def echo(arguments: dict[str, Any]) -> Any:
    return arguments.get("value")


async def validate_json(arguments: dict[str, Any]) -> Any:
    raw = arguments.get("text")
    if not isinstance(raw, str):
        raise ValueError("'text' must be a string")
    return json.loads(raw)


async def read_text_file(arguments: dict[str, Any]) -> Any:
    raw_path = arguments.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("'path' is required")
    path = _safe_workspace_path(raw_path)
    _reject_sensitive(path)
    if not path.is_file():
        raise FileNotFoundError(raw_path)
    if path.stat().st_size > MAX_READ_BYTES:
        raise ValueError("File is too large for this tool")
    return {"path": raw_path, "content": path.read_text(encoding="utf-8")}


async def write_artifact(arguments: dict[str, Any]) -> Any:
    name = arguments.get("name")
    content = arguments.get("content")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("'name' is required")
    if not isinstance(content, str):
        raise ValueError("'content' must be a string")
    content_bytes = content.encode()
    if len(content_bytes) > MAX_ARTIFACT_BYTES:
        raise ValueError("Artifact exceeds maximum allowed size")

    root = get_workspace_root()
    artifact_root = get_artifact_root()
    artifact_root.mkdir(parents=True, exist_ok=True)
    target = (artifact_root / name).resolve()
    if target != artifact_root and artifact_root not in target.parents:
        raise ValueError("Artifact path escapes artifacts directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target.relative_to(root)), "bytes": len(content_bytes)}


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(RegisteredTool("echo", "Return the provided value.", ToolRisk.READ, echo))
    registry.register(
        RegisteredTool("json.validate", "Parse and validate JSON text.", ToolRisk.READ, validate_json)
    )
    registry.register(
        RegisteredTool(
            "file.read_text",
            "Read a non-sensitive UTF-8 text file inside the Agent OS workspace.",
            ToolRisk.READ,
            read_text_file,
        )
    )
    registry.register(
        RegisteredTool(
            "artifact.write",
            "Write generated output under the controlled artifacts directory.",
            ToolRisk.WRITE,
            write_artifact,
        )
    )
    return registry
