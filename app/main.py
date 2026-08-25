from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    description="Agent OS API",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS
# Allow the production Agent OS frontend to access this API.
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
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
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/ready", tags=["system"])
async def readiness() -> JSONResponse:
    checks = await check_readiness()
    healthy = all(value in {"ok", "unconfigured"} for value in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "degraded", "checks": checks},
    )
