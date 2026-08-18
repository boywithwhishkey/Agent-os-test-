from app.api.orchestration import router as orchestration_router
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Agent OS API",
)

app.include_router(api_router)
app.include_router(orchestration_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }

from app.api.phase5 import router as phase5_router
app.include_router(phase5_router)
