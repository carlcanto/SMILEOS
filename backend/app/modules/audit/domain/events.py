from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class AuditEvent:
    """Una acción que debe quedar registrada: quién, qué, sobre qué y desde dónde.

    ``details`` nunca debe contener contraseñas, tokens ni datos clínicos.
    """

    action: str
    actor_user_id: UUID | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    details: dict[str, object] = field(default_factory=dict)
    ip: str | None = None
    request_id: str | None = None
