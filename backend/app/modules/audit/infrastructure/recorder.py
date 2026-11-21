from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.domain.events import AuditEvent
from app.modules.audit.infrastructure.orm import AuditLogRecord


class SqlAuditRecorder:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, event: AuditEvent) -> None:
        self._session.add(
            AuditLogRecord(
                actor_user_id=event.actor_user_id,
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                details=event.details,
                ip=event.ip,
                request_id=event.request_id,
            )
        )
        await self._session.flush()
