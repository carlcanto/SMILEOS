from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.domain.entities import Role
from tests.conftest import (
    DEFAULT_PASSWORD,
    UserFactory,
    bearer,
    login,
    requires_database,
    run_sql,
)

pytestmark = requires_database

NEW_USER: dict[str, Any] = {
    "email": "Recepcion@Example.com",
    "full_name": "  Ana Recepción ",
    "password": "contrasena-recepcion-1",
    "roles": ["recepcion"],
}


def admin_headers(client: TestClient, make_user: UserFactory) -> dict[str, str]:
    make_user()
    return bearer(login(client))


# --- control de acceso por rol ------------------------------------------------------------------


@pytest.mark.parametrize("role", [Role.ODONTOLOGO, Role.RECEPCION])
def test_solo_el_administrador_gestiona_usuarios(
    client: TestClient, make_user: UserFactory, role: Role
) -> None:
    make_user("staff@example.com", roles=(role,))
    headers = bearer(login(client, "staff@example.com"))
    attempts = [
        client.get("/api/v1/users", headers=headers),
        client.post("/api/v1/users", json=NEW_USER, headers=headers),
        client.patch(f"/api/v1/users/{uuid4()}", json={"full_name": "X"}, headers=headers),
        client.post(f"/api/v1/users/{uuid4()}/deactivate", headers=headers),
        client.post(f"/api/v1/users/{uuid4()}/activate", headers=headers),
        client.get("/api/v1/roles", headers=headers),
    ]
    for response in attempts:
        assert response.status_code == 403, response.request.url
        assert response.json()["error"]["code"] == "forbidden"


def test_sin_sesion_no_se_puede_gestionar_usuarios(client: TestClient) -> None:
    assert client.get("/api/v1/users").status_code == 401
    assert client.post("/api/v1/users", json=NEW_USER).status_code == 401


def test_un_usuario_con_varios_roles_pasa_si_alguno_es_admin(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user("jefe@example.com", roles=(Role.ADMIN, Role.ODONTOLOGO))
    headers = bearer(login(client, "jefe@example.com"))
    assert client.get("/api/v1/users", headers=headers).status_code == 200


# --- alta ----------------------------------------------------------------------------------------


def test_el_administrador_crea_un_usuario_que_puede_iniciar_sesion(
    client: TestClient, make_user: UserFactory
) -> None:
    headers = admin_headers(client, make_user)
    response = client.post("/api/v1/users", json=NEW_USER, headers=headers)
    assert response.status_code == 201
    created = response.json()
    assert created["email"] == "recepcion@example.com"
    assert created["full_name"] == "Ana Recepción"
    assert created["roles"] == ["recepcion"]
    assert created["is_active"] is True
    assert "password" not in str(created).lower()
    login(client, "recepcion@example.com", NEW_USER["password"])


def test_correo_repetido_da_409_sin_importar_mayusculas(
    client: TestClient, make_user: UserFactory
) -> None:
    headers = admin_headers(client, make_user)
    assert client.post("/api/v1/users", json=NEW_USER, headers=headers).status_code == 201
    again = client.post(
        "/api/v1/users", json={**NEW_USER, "email": "RECEPCION@example.com"}, headers=headers
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "email_already_exists"


def test_contrasena_debil_en_el_alta_da_422(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    response = client.post("/api/v1/users", json={**NEW_USER, "password": "corta"}, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "weak_password"


@pytest.mark.parametrize(
    "change",
    [{"roles": ["superusuario"]}, {"roles": []}, {"email": "sin-arroba"}, {"full_name": ""}],
)
def test_datos_invalidos_en_el_alta_dan_422(
    client: TestClient, make_user: UserFactory, change: dict[str, object]
) -> None:
    headers = admin_headers(client, make_user)
    response = client.post("/api/v1/users", json={**NEW_USER, **change}, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# --- listado y roles -----------------------------------------------------------------------------


def test_listado_con_paginacion_y_filtro(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    for number in range(4):
        client.post(
            "/api/v1/users",
            json={**NEW_USER, "email": f"user{number}@example.com"},
            headers=headers,
        )
    page = client.get("/api/v1/users?page=1&per_page=2", headers=headers).json()
    assert page["total"] == 5 and page["per_page"] == 2 and len(page["items"]) == 2
    last = client.get("/api/v1/users?page=3&per_page=2", headers=headers).json()
    assert len(last["items"]) == 1
    run_sql("UPDATE users SET is_active = false WHERE email = 'user0@example.com'")
    inactive = client.get("/api/v1/users?active=false", headers=headers).json()
    assert [item["email"] for item in inactive["items"]] == ["user0@example.com"]
    assert client.get("/api/v1/users?per_page=1000", headers=headers).status_code == 422


def test_listado_de_roles(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    roles = client.get("/api/v1/roles", headers=headers).json()
    assert [role["code"] for role in roles] == ["admin", "odontologo", "recepcion"]
    assert all(role["description"] for role in roles)


# --- edición -------------------------------------------------------------------------------------


def test_editar_nombre_y_roles(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    user_id = client.post("/api/v1/users", json=NEW_USER, headers=headers).json()["id"]
    response = client.patch(
        f"/api/v1/users/{user_id}",
        json={"full_name": "Ana María", "roles": ["recepcion", "odontologo"]},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Ana María"
    assert response.json()["roles"] == ["odontologo", "recepcion"]


def test_un_cambio_de_rol_aplica_a_la_sesion_vigente(
    client: TestClient, make_user: UserFactory
) -> None:
    headers = admin_headers(client, make_user)
    client.post("/api/v1/users", json={**NEW_USER, "roles": ["admin"]}, headers=headers)
    staff = bearer(login(client, "recepcion@example.com", NEW_USER["password"]))
    assert client.get("/api/v1/users", headers=staff).status_code == 200
    user_id = run_sql("SELECT id FROM users WHERE email = 'recepcion@example.com'")[0][0]
    client.patch(f"/api/v1/users/{user_id}", json={"roles": ["recepcion"]}, headers=headers)
    assert client.get("/api/v1/users", headers=staff).status_code == 403


def test_usuario_inexistente_da_404(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    response = client.patch(f"/api/v1/users/{uuid4()}", json={"full_name": "X"}, headers=headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "user_not_found"
    assert client.patch("/api/v1/users/no-es-uuid", json={}, headers=headers).status_code == 422


# --- desactivar y reactivar ---------------------------------------------------------------------


def test_desactivar_cierra_sus_sesiones_y_reactivar_lo_deja_volver(
    client: TestClient, make_user: UserFactory
) -> None:
    headers = admin_headers(client, make_user)
    created = client.post("/api/v1/users", json=NEW_USER, headers=headers).json()
    staff = login(client, "recepcion@example.com", NEW_USER["password"])

    off = client.post(f"/api/v1/users/{created['id']}/deactivate", headers=headers)
    assert off.status_code == 200 and off.json()["is_active"] is False
    assert client.get("/api/v1/auth/me", headers=bearer(staff)).status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": staff["refresh_token"]}
        ).status_code
        == 401
    )

    on = client.post(f"/api/v1/users/{created['id']}/activate", headers=headers)
    assert on.json()["is_active"] is True
    login(client, "recepcion@example.com", NEW_USER["password"])


def test_nadie_puede_desactivarse_a_si_mismo(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    admin = login(client)
    response = client.post(f"/api/v1/users/{admin['user']['id']}/deactivate", headers=bearer(admin))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "self_deactivation"


def test_siempre_queda_un_administrador_activo(client: TestClient, make_user: UserFactory) -> None:
    make_user("a@example.com")
    make_user("b@example.com")
    a, b = login(client, "a@example.com"), login(client, "b@example.com")

    # Con dos administradores, uno puede desactivar al otro...
    assert (
        client.post(f"/api/v1/users/{a['user']['id']}/deactivate", headers=bearer(b)).status_code
        == 200
    )
    # ...pero el último ya no puede quitarse el rol ni desactivarse.
    quitar_rol = client.patch(
        f"/api/v1/users/{b['user']['id']}", json={"roles": ["recepcion"]}, headers=bearer(b)
    )
    assert quitar_rol.status_code == 409
    assert quitar_rol.json()["error"]["code"] == "last_admin"
    assert run_sql("SELECT count(*) FROM users WHERE is_active")[0][0] == 1


def test_la_contrasena_inicial_no_se_devuelve_nunca(
    client: TestClient, make_user: UserFactory
) -> None:
    headers = admin_headers(client, make_user)
    client.post("/api/v1/users", json=NEW_USER, headers=headers)
    listing = client.get("/api/v1/users", headers=headers).text
    assert NEW_USER["password"] not in listing
    assert DEFAULT_PASSWORD not in listing
    assert "argon2" not in listing


def test_desactivar_y_activar_son_idempotentes(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    user_id = client.post("/api/v1/users", json=NEW_USER, headers=headers).json()["id"]
    assert client.post(f"/api/v1/users/{user_id}/activate", headers=headers).json()["is_active"]
    for _ in range(2):
        response = client.post(f"/api/v1/users/{user_id}/deactivate", headers=headers)
        assert response.status_code == 200 and response.json()["is_active"] is False
    actions = [row[0] for row in run_sql("SELECT action FROM audit_log")]
    assert actions.count("user_deactivated") == 1
    assert "user_activated" not in actions


def test_editar_sin_cambios_no_genera_auditoria(client: TestClient, make_user: UserFactory) -> None:
    headers = admin_headers(client, make_user)
    created = client.post("/api/v1/users", json=NEW_USER, headers=headers).json()
    before = run_sql("SELECT count(*) FROM audit_log")[0][0]
    client.patch(
        f"/api/v1/users/{created['id']}",
        json={"full_name": created["full_name"], "roles": created["roles"]},
        headers=headers,
    )
    assert run_sql("SELECT count(*) FROM audit_log")[0][0] == before
