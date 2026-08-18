from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.tools.models import ToolRisk
from app.tools.registry import RegisteredTool, ToolRegistry

WORKSPACE_ROOT = Path.cwd().resolve()
ARTIFACT_ROOT = (WORKSPACE_ROOT / "artifacts").resolve()


def _safe_workspace_path(value: str) -> Path:
    path = (WORKSPACE_ROOT / value).resolve()
    if path != WORKSPACE_ROOT and WORKSPACE_ROOT not in path.parents:
        raise ValueError("Path escapes the workspace")
    return path


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
    if not path.is_file():
        raise FileNotFoundError(raw_path)
    if path.stat().st_size > 1_000_000:
        raise ValueError("File is too large for this tool")
    return {"path": raw_path, "content": path.read_text(encoding="utf-8")}


async def write_artifact(arguments: dict[str, Any]) -> Any:
    name = arguments.get("name")
    content = arguments.get("content")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("'name' is required")
    if not isinstance(content, str):
        raise ValueError("'content' must be a string")

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    target = (ARTIFACT_ROOT / name).resolve()
    if target != ARTIFACT_ROOT and ARTIFACT_ROOT not in target.parents:
        raise ValueError("Artifact path escapes artifacts directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target.relative_to(WORKSPACE_ROOT)), "bytes": len(content.encode())}


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(RegisteredTool("echo", "Return the provided value.", ToolRisk.READ, echo))
    registry.register(
        RegisteredTool("json.validate", "Parse and validate JSON text.", ToolRisk.READ, validate_json)
    )
    registry.register(
        RegisteredTool(
            "file.read_text",
            "Read a UTF-8 text file inside the Agent OS workspace.",
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
