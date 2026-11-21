import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.modules.identity.infrastructure.security import (
    Argon2PasswordHasher,
    JwtAccessTokenService,
    SecureTokenGenerator,
)
from app.shared.domain import DomainError
from tests.conftest import TEST_JWT_SECRET


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 11, 21, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current


def service(clock: FakeClock, minutes: int = 15) -> JwtAccessTokenService:
    return JwtAccessTokenService(TEST_JWT_SECRET, minutes, clock)


def test_argon2_verifica_la_contrasena_correcta_y_rechaza_otras() -> None:
    hasher = Argon2PasswordHasher()

    async def scenario() -> None:
        hashed = await hasher.hash("contrasena-correcta")
        assert hashed.startswith("$argon2id$")
        assert await hasher.verify(hashed, "contrasena-correcta")
        assert not await hasher.verify(hashed, "otra-contrasena")

    asyncio.run(scenario())


def test_argon2_no_repite_el_hash_de_la_misma_contrasena() -> None:
    hasher = Argon2PasswordHasher()

    async def scenario() -> None:
        assert await hasher.hash("misma-contrasena") != await hasher.hash("misma-contrasena")

    asyncio.run(scenario())


def test_verificar_sin_hash_siempre_falla_pero_hace_el_trabajo() -> None:
    hasher = Argon2PasswordHasher()

    async def scenario() -> None:
        assert not await hasher.verify(None, "cualquier-cosa")
        assert not await hasher.verify("esto-no-es-un-hash", "cualquier-cosa")

    asyncio.run(scenario())


def test_un_hash_recien_creado_no_necesita_actualizarse() -> None:
    hasher = Argon2PasswordHasher()
    hashed = asyncio.run(hasher.hash("contrasena-correcta"))
    assert not hasher.needs_rehash(hashed)


def test_token_de_acceso_ida_y_vuelta() -> None:
    clock = FakeClock()
    user_id = uuid4()
    token, expires_in = service(clock).issue(user_id)
    assert expires_in == 15 * 60
    assert service(clock).decode(token) == user_id


def test_token_de_acceso_expira_segun_el_reloj_inyectado() -> None:
    clock = FakeClock()
    token, _ = service(clock).issue(uuid4())
    clock.current += timedelta(minutes=14, seconds=59)
    service(clock).decode(token)
    clock.current += timedelta(seconds=1)
    with pytest.raises(DomainError) as error:
        service(clock).decode(token)
    assert error.value.code == "invalid_token"


def test_token_firmado_con_otra_clave_se_rechaza() -> None:
    clock = FakeClock()
    forged = JwtAccessTokenService("otra-clave-distinta-de-mas-de-32-caracteres", 15, clock)
    token, _ = forged.issue(uuid4())
    with pytest.raises(DomainError):
        service(clock).decode(token)


@pytest.mark.parametrize("garbage", ["", "no-es-un-jwt", "a.b.c"])
def test_basura_se_rechaza_sin_romperse(garbage: str) -> None:
    with pytest.raises(DomainError) as error:
        service(FakeClock()).decode(garbage)
    assert error.value.code == "invalid_token"


def _encode(claims: dict[str, object], algorithm: str = "HS256") -> str:
    return jwt.encode(claims, TEST_JWT_SECRET, algorithm=algorithm)


def test_token_de_otro_tipo_se_rechaza() -> None:
    clock = FakeClock()
    now = int(clock.now().timestamp())
    token = _encode({"sub": str(uuid4()), "typ": "refresh", "iat": now, "exp": now + 600})
    with pytest.raises(DomainError):
        service(clock).decode(token)


def test_token_sin_alguna_reclamacion_obligatoria_se_rechaza() -> None:
    clock = FakeClock()
    now = int(clock.now().timestamp())
    token = _encode({"sub": str(uuid4()), "typ": "access", "exp": now + 600})  # sin iat
    with pytest.raises(DomainError):
        service(clock).decode(token)


def test_token_con_sub_que_no_es_uuid_se_rechaza() -> None:
    clock = FakeClock()
    now = int(clock.now().timestamp())
    token = _encode({"sub": "no-es-uuid", "typ": "access", "iat": now, "exp": now + 600})
    with pytest.raises(DomainError):
        service(clock).decode(token)


def test_token_sin_firma_alg_none_se_rechaza() -> None:
    clock = FakeClock()
    now = int(clock.now().timestamp())
    token = jwt.encode(
        {"sub": str(uuid4()), "typ": "access", "iat": now, "exp": now + 600},
        key=None,
        algorithm="none",
    )
    with pytest.raises(DomainError):
        service(clock).decode(token)


def test_token_de_refresco_es_aleatorio_y_su_hash_estable() -> None:
    generator = SecureTokenGenerator()
    first, second = generator.generate(), generator.generate()
    assert first != second
    assert len(first) >= 64
    assert generator.hash(first) == generator.hash(first)
    assert generator.hash(first) != generator.hash(second)
    assert len(generator.hash(first)) == 64
    assert first not in generator.hash(first)


def test_token_emitido_en_el_futuro_se_rechaza() -> None:
    clock = FakeClock()
    now = int(clock.now().timestamp())
    token = _encode({"sub": str(uuid4()), "typ": "access", "iat": now + 3600, "exp": now + 7200})
    with pytest.raises(DomainError):
        service(clock).decode(token)
