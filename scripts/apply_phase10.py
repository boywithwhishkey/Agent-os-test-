from pathlib import Path

def append_once(path: Path, text: str):
    current = path.read_text() if path.exists() else ""
    if text not in current:
        if current and not current.endswith("\n"):
            current += "\n"
        current += text + "\n"
        path.write_text(current)

main = Path("app/main.py")
append_once(main, "from app.api.phase10 import router as phase10_router")
append_once(main, "app.include_router(phase10_router)")

env = Path(".env.example")
for line in [
    "AGENT_OS_CIRCUIT_FAILURES=3",
    "AGENT_OS_CIRCUIT_RECOVERY_SECONDS=30",
    "AGENT_OS_INTEGRATION_RATE_LIMIT=60",
    "AGENT_OS_INTEGRATION_RATE_WINDOW=60",
    "AGENT_OS_RETRY_BACKOFF_BASE=0.25",
]:
    append_once(env, line)

gitignore = Path(".gitignore")
for line in [
    "*.egg-info/",
    "dist/",
    "build/",
    "agent-os-current.zip",
    "agent-os-*.zip",
    "artifacts/",
    "infra/n8n/agent-os-n8n-workflow.json",
    "infra/n8n/.env",
    "infra/n8n/data/",
]:
    append_once(gitignore, line)

print("Phase 10 integration and repository hygiene applied.")
