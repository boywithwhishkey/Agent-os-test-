from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.orchestration import router as orchestration_router
from app.api.phase5 import router as phase5_router
from app.api.phase6 import router as phase6_router
from app.api.phase7 import router as phase7_router
from app.api.phase8 import router as phase8_router
from app.api.phase9 import router as phase9_router
from app.api.phase10 import router as phase10_router
from app.api.router import api_router
from app.core import lifecycle
from app.core.config import settings
from app.core.correlation import CORRELATION_HEADER, get_or_create_correlation_id
from app.core.readiness import check_readiness


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await lifecycle.close_all()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="THYNACT API",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# Allow the production THYNACT frontend to access this API.
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", CORRELATION_HEADER],
    expose_headers=[CORRELATION_HEADER],
)


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = get_or_create_correlation_id(request.headers.get(CORRELATION_HEADER))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers[CORRELATION_HEADER] = correlation_id
    return response


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc).strip("'")})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    return JSONResponse(status_code=504, content={"detail": "Request timed out"})


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "backends": {
            "memory": settings.memory_backend,
            "task": settings.task_backend,
            "workflow": settings.workflow_backend,
            "workflow_definition": settings.workflow_definition_backend,
            "runtime": settings.runtime_backend,
            "tool": settings.tool_backend,
            "queue": settings.queue_backend,
        },
    }


@app.get("/ready", tags=["system"])
async def readiness() -> JSONResponse:
    checks = await check_readiness()
    healthy = all(value in {"ok", "unconfigured"} for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "degraded", "checks": checks},
    )


# ---------------------------------------------------------
# Frontend (production only)
# In dev, Vite serves the frontend on its own port. In production there is
# a single process, so if a built frontend is present we serve it here and
# fall back to index.html for client-side routes.
# ---------------------------------------------------------

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
