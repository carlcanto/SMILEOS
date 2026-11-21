"""Adaptadores de seguridad: contraseñas con Argon2, tokens de acceso JWT y de refresco."""

import asyncio
import hashlib
import secrets
from datetime import timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher as Argon2
from argon2.exceptions import InvalidHashError, VerificationError

from app.shared.domain import DomainError
from app.shared.ports import Clock

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
# Tolerancia ante relojes un poco desfasados entre quien emite y quien valida el token.
CLOCK_SKEW_SECONDS = 60


class Argon2PasswordHasher:
    """Argon2id con los parámetros por defecto de ``argon2-cffi`` (perfil de RFC 9106).

    El cálculo usa CPU y memoria a propósito, así que corre en un hilo para no
    bloquear el ciclo de eventos de la API.
    """

    def __init__(self) -> None:
        self._argon2 = Argon2()
        # Hash falso para que "el usuario no existe" tarde lo mismo que "contraseña mala".
        self._dummy_hash = self._argon2.hash("contrasena-falsa-para-igualar-tiempos")

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._argon2.hash, password)

    async def verify(self, password_hash: str | None, password: str) -> bool:
        target = password_hash or self._dummy_hash
        try:
            await asyncio.to_thread(self._argon2.verify, target, password)
        except (VerificationError, InvalidHashError):
            return False
        return password_hash is not None

    def needs_rehash(self, password_hash: str) -> bool:
        return self._argon2.check_needs_rehash(password_hash)


class JwtAccessTokenService:
    """Token de acceso de vida corta firmado con HS256.

    Solo lleva el id del usuario: los roles y el estado activo se leen de la base en cada
    petición, así que un cambio de rol o una desactivación aplican de inmediato.
    """

    def __init__(self, secret: str, minutes: int, clock: Clock) -> None:
        self._secret = secret
        self._ttl = timedelta(minutes=minutes)
        self._clock = clock

    def issue(self, user_id: UUID) -> tuple[str, int]:
        now = self._clock.now()
        payload = {
            "sub": str(user_id),
            "typ": ACCESS_TOKEN_TYPE,
            "iat": int(now.timestamp()),
            "exp": int((now + self._ttl).timestamp()),
            "jti": uuid4().hex,
        }
        token = jwt.encode(payload, self._secret, algorithm=JWT_ALGORITHM)
        return token, int(self._ttl.total_seconds())

    def decode(self, token: str) -> UUID:
        invalid = DomainError("invalid_token", "La sesión no es válida o expiró.")
        try:
            # Las fechas (exp, iat) se comparan con el reloj inyectado, no con el del sistema.
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[JWT_ALGORITHM],
                options={
                    "verify_exp": False,
                    "verify_iat": False,
                    "require": ["sub", "exp", "iat", "typ"],
                },
            )
            now = int(self._clock.now().timestamp())
            if claims["typ"] != ACCESS_TOKEN_TYPE:
                raise invalid
            if claims["exp"] <= now or claims["iat"] > now + CLOCK_SKEW_SECONDS:
                raise invalid
            return UUID(claims["sub"])
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise invalid from error


class SecureTokenGenerator:
    """Token de refresco opaco: 48 bytes aleatorios; en la base solo se guarda su SHA-256."""

    def generate(self) -> str:
        return secrets.token_urlsafe(48)

    def hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
