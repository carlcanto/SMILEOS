from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class Role(StrEnum):
    ADMIN = "admin"
    ODONTOLOGO = "odontologo"
    RECEPCION = "recepcion"


ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.ADMIN: "Administra usuarios, configuración, reportes y auditoría.",
    Role.ODONTOLOGO: "Atiende pacientes y gestiona el expediente clínico.",
    Role.RECEPCION: "Registra pacientes, agenda citas y cobra.",
}


@dataclass
class User:
    id: UUID
    email: str
    full_name: str
    password_hash: str
    is_active: bool
    roles: frozenset[Role]
    created_at: datetime
    last_login_at: datetime | None = None

    def has_any_role(self, *roles: Role) -> bool:
        return bool(self.roles & set(roles))


@dataclass(frozen=True)
class RefreshToken:
    """Token de refresco guardado solo como hash; se rota en cada uso."""

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
