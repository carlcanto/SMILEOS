"""Proceso ``worker``: misma imagen que la API, otro comando (``python -m app.worker``).

En S0 es un esqueleto: arranca, comprueba la base de datos en cada ciclo y se
detiene de forma ordenada ante SIGTERM o SIGINT. En S7 cada ciclo procesará la
cola ``notification_outbox``.
"""

import asyncio
import logging
import signal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.shared.config import Settings, get_settings
from app.shared.db import create_engine
from app.shared.logging import configure_logging

logger = logging.getLogger("app.worker")


async def run_cycle(engine: AsyncEngine) -> None:
    """Un ciclo de trabajo. Hoy solo verifica que la base responde."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    logger.debug("worker_cycle_ok")


async def run(settings: Settings, stop: asyncio.Event) -> None:
    engine = create_engine(settings.database_url)
    logger.info(
        "worker_started",
        extra={"profile": settings.app_profile, "poll_seconds": settings.worker_poll_seconds},
    )
    try:
        while not stop.is_set():
            try:
                await run_cycle(engine)
            except Exception:
                # Un ciclo fallido no debe tumbar el proceso: se reintenta en el siguiente.
                logger.exception("worker_cycle_failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=settings.worker_poll_seconds)
            except TimeoutError:
                continue
    finally:
        await engine.dispose()
        logger.info("worker_stopped")


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(signum, stop.set)
    await run(settings, stop)


if __name__ == "__main__":
    asyncio.run(main())
