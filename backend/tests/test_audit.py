import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError

from tests.conftest import (
    DEFAULT_PASSWORD,
    OTHER_PASSWORD,
    UserFactory,
    bearer,
    login,
    requires_database,
    run_sql,
)

pytestmark = requires_database


def test_las_acciones_de_administracion_quedan_auditadas(
    client: TestClient, make_user: UserFactory
) -> None:
    admin = make_user()
    headers = bearer(login(client))
    created = client.post(
        "/api/v1/users",
        json={
            "email": "nuevo@example.com",
            "full_name": "Nuevo",
            "password": OTHER_PASSWORD,
            "roles": ["recepcion"],
        },
        headers={**headers, "X-Request-ID": "req-alta-1"},
    ).json()
    client.post(f"/api/v1/users/{created['id']}/deactivate", headers=headers)
    client.post(f"/api/v1/users/{created['id']}/activate", headers=headers)
    client.patch(f"/api/v1/users/{created['id']}", json={"full_name": "Otro"}, headers=headers)

    actions = [row[0] for row in run_sql("SELECT action FROM audit_log ORDER BY occurred_at, id")]
    assert actions == [
        "user_created",  # el alta del administrador, hecha por el CLI
        "login_success",
        "user_created",
        "user_deactivated",
        "user_activated",
        "user_updated",
    ]
    row = run_sql(
        "SELECT actor_user_id::text, entity_id, request_id, details->>'via' "
        "FROM audit_log WHERE action = 'user_created' ORDER BY occurred_at DESC, id LIMIT 1"
    )[0]
    assert row[0] == str(admin.id)
    assert row[1] == created["id"]
    assert row[2] == "req-alta-1"
    assert row[3] == "api"


def test_la_auditoria_nunca_contiene_contrasenas_ni_tokens(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    tokens = login(client)
    client.post(
        "/api/v1/auth/change-password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": OTHER_PASSWORD},
        headers=bearer(tokens),
    )
    everything = str(run_sql("SELECT * FROM audit_log"))
    for secret in (
        DEFAULT_PASSWORD,
        OTHER_PASSWORD,
        tokens["access_token"],
        tokens["refresh_token"],
        "argon2",
    ):
        assert secret not in everything


def test_la_bitacora_no_se_puede_modificar(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    with pytest.raises(DBAPIError, match="solo insercion"):
        run_sql("UPDATE audit_log SET action = 'otra-cosa'")


def test_la_bitacora_no_se_puede_borrar(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    with pytest.raises(DBAPIError, match="solo insercion"):
        run_sql("DELETE FROM audit_log")
    assert run_sql("SELECT count(*) FROM audit_log")[0][0] >= 1


def test_un_usuario_con_auditoria_no_se_puede_borrar(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    login(client)
    with pytest.raises(DBAPIError):
        run_sql("DELETE FROM users")
