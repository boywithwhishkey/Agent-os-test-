from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.orchestration import router as orchestration_router
from app.api.router import api_router
from app.core.config import settings

from app.api.phase5 import router as phase5_router
from app.api.phase6 import router as phase6_router
from app.api.phase7 import router as phase7_router
from app.api.phase8 import router as phase8_router
from app.api.phase9 import router as phase9_router
from app.api.phase10 import router as phase10_router


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Agent OS API",
)


# ---------------------------------------------------------
# CORS
# Allow the production Agent OS frontend to access this API.
# ---------------------------------------------------------

ALLOWED_ORIGINS = [
    "https://agent-os-test.pages.dev",
    "https://app.thynact.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ---------------------------------------------------------
# API Routers
# ---------------------------------------------------------

app.include_router(api_router)
app.include_router(orchestration_router)

app.include_router(phase5_router)
app.include_router(phase6_router)
app.include_router(phase7_router)
app.include_router(phase8_router)
app.include_router(phase9_router)
app.include_router(phase10_router)


# ---------------------------------------------------------
# System Health
# ---------------------------------------------------------

@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
