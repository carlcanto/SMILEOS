"""Puertos comunes: lo que el negocio necesita del exterior y no quiere conocer."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Instante actual, siempre con zona horaria UTC."""
        ...


class UnitOfWork(Protocol):
    """Quien ejecuta el caso de uso decide cuándo confirmar la transacción."""

    async def commit(self) -> None: ...
