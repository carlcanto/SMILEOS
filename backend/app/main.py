"""Punto de entrada de la API: ``uvicorn app.main:create_app --factory``."""

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import ensure_bootstrap_admin
from app.migrations import upgrade_to_head
from app.modules.identity.api.router import router as identity_router
from app.modules.identity.composition import build_runtime
from app.shared import health, public_config
from app.shared.config import Settings, get_settings
from app.shared.db import create_engine, create_session_factory
from app.shared.errors import register_error_handlers
from app.shared.logging import configure_logging, request_id_var

logger = logging.getLogger("app.access")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        app.state.settings = settings
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        app.state.identity = build_runtime(settings)
        if settings.run_migrations_on_start:
            # Alembic usa su propio ciclo de eventos: se ejecuta en un hilo aparte.
            await asyncio.to_thread(upgrade_to_head, settings.database_url)
            logger.info("migrations_applied")
        if await ensure_bootstrap_admin(settings, app.state.identity, app.state.session_factory):
            logger.info("bootstrap_admin_created")
        logger.info("api_started", extra={"profile": settings.app_profile})
        yield
        await engine.dispose()

    app = FastAPI(title="SmileOS API", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        # Solo ruta, método y estado: sin parámetros de consulta ni cuerpo.
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                "request_id": request_id,
            },
        )
        return response

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(public_config.router)
    app.include_router(identity_router)
    return app
