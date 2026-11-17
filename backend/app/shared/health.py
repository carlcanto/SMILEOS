"""Salud del sistema: ``/health`` (el proceso vive) y ``/health/ready`` (la base responde)."""

import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.shared.config import Settings

logger = logging.getLogger("app.health")

router = APIRouter(tags=["system"])

READY_TIMEOUT_SECONDS = 3.0


@router.get("/health")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", response_model=None)
async def ready(request: Request) -> dict[str, str] | JSONResponse:
    settings: Settings = request.app.state.settings
    try:
        async with asyncio.timeout(READY_TIMEOUT_SECONDS):
            async with request.app.state.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except Exception:
        logger.warning("ready_check_failed", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "down", "profile": settings.app_profile},
        )
    return {"status": "ok", "database": "up", "profile": settings.app_profile}
