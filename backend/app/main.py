"""FastAPI main application entry point for CodeSentinel."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.api.routes import auth, repos, scans, findings, webhooks, assistant, validations, trends

logger = structlog.get_logger()

app = FastAPI(
    title="CodeSentinel API",
    description="Context-Aware Security Intelligence Platform for DevSecOps",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(repos.router, prefix="/api", tags=["Repositories"])
app.include_router(scans.router, prefix="/api", tags=["Scans"])
app.include_router(findings.router, prefix="/api", tags=["Findings"])
app.include_router(validations.router, prefix="/api", tags=["Patch Validation"])
app.include_router(assistant.router, prefix="/api", tags=["AI Assistant"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(trends.router, tags=["Trends"])


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "app": settings.APP_NAME, "env": settings.APP_ENV}


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("CodeSentinel backend starting", env=settings.APP_ENV)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("CodeSentinel backend shutting down")
