import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.modules.identity.domain.entities import Role, User
from app.modules.identity.infrastructure.repositories import SqlUserRepository
from app.shared.config import Settings
from app.shared.db import create_engine, create_session_factory
from app.shared.domain import DomainError
from tests.conftest import requires_database, run_sql

pytestmark = requires_database


def make_user(email: str) -> User:
    return User(
        id=uuid4(),
        email=email,
        full_name="Persona de Prueba",
        password_hash="hash-de-prueba",
        is_active=True,
        roles=frozenset({Role.RECEPCION}),
        created_at=datetime.now(UTC),
    )


def test_dos_altas_simultaneas_con_el_mismo_correo_las_decide_la_base(
    settings: Settings, clean_database: None
) -> None:
    """Verificar "¿existe?" y luego insertar deja una carrera; la llave única la cierra."""

    async def scenario() -> None:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)
        try:
            async with factory() as first, factory() as second:
                await SqlUserRepository(first).add(make_user("dup@example.com"))
                # La segunda alta espera a que la primera confirme, y entonces choca.
                racing = asyncio.create_task(
                    SqlUserRepository(second).add(make_user("dup@example.com"))
                )
                await asyncio.sleep(0.3)
                assert not racing.done()
                await first.commit()
                with pytest.raises(DomainError) as error:
                    await racing
                assert error.value.code == "email_already_exists"
        finally:
            await engine.dispose()

    asyncio.run(scenario())
    assert run_sql("SELECT count(*) FROM users WHERE email = 'dup@example.com'")[0][0] == 1


def test_la_base_rechaza_correos_con_mayusculas(clean_database: None) -> None:
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError, match="email_lowercase"):
        run_sql(
            "INSERT INTO users (id, email, full_name, password_hash) "
            "VALUES (gen_random_uuid(), 'Mayus@Example.com', 'X', 'h')"
        )
