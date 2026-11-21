"""Adaptadores comunes de los puertos de ``app.shared.ports``."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class SqlUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()
