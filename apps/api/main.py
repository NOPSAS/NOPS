"""
ByggSjekk – FastAPI application entry point.

Run locally:
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import init_db

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup / shutdown logic."""
    logger.info("ByggSjekk API starting up (env=%s)", settings.ENVIRONMENT)
    await init_db()
    logger.info("Database initialised.")
    from app.services.rule_seeder import seed_rules_if_empty
    from app.db.base import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await seed_rules_if_empty(db)
    yield
    logger.info("ByggSjekk API shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        description=(
            "ByggSjekk – Norwegian SaaS platform for architects. "
            "Automated building regulation compliance checking."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ---- CORS ----
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Routers ----
    application.include_router(api_router, prefix="/api/v1")

    # ---- Exception handlers ----
    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Validation error on %s: %s", request.url, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    # ---- Health check ----
    @application.get("/health", tags=["System"], summary="Health check")
    async def health() -> dict:
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "tjenester": 20,
            "endepunkter": 30,
        }

    return application


app = create_app()
