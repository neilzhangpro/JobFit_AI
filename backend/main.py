"""JobFit AI — FastAPI Application Entry Point.

Initializes the FastAPI application, registers routers from all bounded contexts,
and configures middleware (auth, tenant, rate limiting).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    settings = get_settings()
    print(f"Starting JobFit AI [{settings.app_env}] ...")
    # TODO(#4): Initialize DB pool, event bus, etc.
    yield
    # Shutdown
    print("Shutting down JobFit AI ...")
    # TODO(#4): Close DB pool, cleanup resources


app = FastAPI(
    title="JobFit AI",
    description="Intelligent Resume Optimization Agent API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not get_settings().is_production else None,
    redoc_url="/redoc" if not get_settings().is_production else None,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health Check ---
@app.get("/api/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Health check endpoint to verify the service is running."""
    return {"status": "ok", "service": "jobfit-ai-backend"}


# --- Router Registration ---
# TODO(#1): Register routers as they are implemented:
# app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
# app.include_router(resume_router, prefix="/api/resumes", tags=["Resumes"])
# app.include_router(optimize_router, prefix="/api", tags=["Optimization"])
# app.include_router(interview_router, prefix="/api", tags=["Interview"])
# app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])
