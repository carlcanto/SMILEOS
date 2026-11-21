from typing import Protocol

from app.modules.audit.domain.events import AuditEvent


class AuditRecorder(Protocol):
    async def record(self, event: AuditEvent) -> None:
        """Registra el evento dentro de la transacción en curso (no hace ``commit``)."""
        ...
