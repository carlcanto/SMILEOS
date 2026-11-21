from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

from app.modules.identity.domain.entities import Role
from tests.conftest import (
    DEFAULT_PASSWORD,
    TEST_JWT_SECRET,
    UserFactory,
    bearer,
    login,
    requires_database,
    run_sql,
)

pytestmark = requires_database


def audit_actions() -> list[str]:
    return [row[0] for row in run_sql("SELECT action FROM audit_log ORDER BY occurred_at, id")]


# --- login ---------------------------------------------------------------------------------


def test_login_correcto_entrega_tokens_y_usuario(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    body = login(client)
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == "admin@example.com"
    assert body["user"]["roles"] == ["admin"]
    assert "password" not in str(body).lower()
    assert body["user"]["last_login_at"] is not None


def test_login_ignora_mayusculas_y_espacios_del_correo(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    login(client, email="  ADMIN@Example.COM ")


def test_login_fallido_responde_igual_para_correo_inexistente_y_contrasena_mala(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    wrong_password = client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "otra-contrasena-1"}
    )
    unknown_user = client.post(
        "/api/v1/auth/login", json={"email": "nadie@example.com", "password": "otra-contrasena-1"}
    )
    for response in (wrong_password, unknown_user):
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_credentials"
        assert response.headers["www-authenticate"] == "Bearer"
    assert wrong_password.json()["error"]["message"] == unknown_user.json()["error"]["message"]


def test_login_de_usuario_desactivado_falla(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    run_sql("UPDATE users SET is_active = false")
    response = client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": DEFAULT_PASSWORD}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_login_registra_auditoria_sin_guardar_la_contrasena(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "intento-fallido-secreto"},
        headers={"X-Request-ID": "req-login-1"},
    )
    login(client)
    assert audit_actions()[-2:] == ["login_failed", "login_success"]
    rows = run_sql("SELECT details::text, request_id, entity_id FROM audit_log")
    assert "intento-fallido-secreto" not in str(rows)
    assert any(row[1] == "req-login-1" for row in rows)
    assert run_sql("SELECT details->>'reason' FROM audit_log WHERE action = 'login_failed'") == [
        ("bad_password",)
    ]


def test_login_con_cuerpo_invalido_da_422_sin_devolver_el_valor(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"email": "sin-arroba", "password": "x"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert "sin-arroba" not in response.text


# --- me y validación del token -------------------------------------------------------------


def test_me_devuelve_el_usuario_de_la_sesion(client: TestClient, make_user: UserFactory) -> None:
    make_user(roles=(Role.ODONTOLOGO,))
    tokens = login(client)
    response = client.get("/api/v1/auth/me", headers=bearer(tokens))
    assert response.status_code == 200
    assert response.json()["roles"] == ["odontologo"]


def test_me_sin_token_da_401_not_authenticated(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_con_token_basura_da_401_invalid_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer basura"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def _forged(user_id: str, *, secret: str = TEST_JWT_SECRET, expires_in: int = 600) -> str:
    now = int(datetime.now(UTC).timestamp())
    claims = {"sub": user_id, "typ": "access", "iat": now, "exp": now + expires_in}
    return jwt.encode(claims, secret, algorithm="HS256")


def test_token_expirado_se_rechaza(client: TestClient, make_user: UserFactory) -> None:
    user = make_user()
    token = _forged(str(user.id), expires_in=-10)
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_firmado_con_otra_clave_se_rechaza(
    client: TestClient, make_user: UserFactory
) -> None:
    user = make_user()
    token = _forged(str(user.id), secret="otra-clave-distinta-de-mas-de-32-caracteres")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_de_un_usuario_inexistente_se_rechaza(client: TestClient) -> None:
    token = _forged(str(uuid4()))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"


def test_al_desactivar_un_usuario_su_token_deja_de_servir_de_inmediato(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    tokens = login(client)
    assert client.get("/api/v1/auth/me", headers=bearer(tokens)).status_code == 200
    run_sql("UPDATE users SET is_active = false")
    assert client.get("/api/v1/auth/me", headers=bearer(tokens)).status_code == 401


# --- refresh --------------------------------------------------------------------------------


def refresh(client: TestClient, token: str) -> int:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    return int(response.status_code)


def test_refresh_rota_el_token_y_entrega_uno_nuevo(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    first = login(client)
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert response.status_code == 200
    second = response.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert client.get("/api/v1/auth/me", headers=bearer(second)).status_code == 200


def test_reusar_un_refresh_ya_usado_revoca_todas_las_sesiones(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    first = login(client)
    second = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()
    # Quien presenta el token viejo (por ejemplo un ladrón) dispara la alarma...
    assert refresh(client, first["refresh_token"]) == 401
    # ...y el token nuevo, que era legítimo, también queda revocado.
    assert refresh(client, second["refresh_token"]) == 401
    assert "refresh_reuse_detected" in audit_actions()


def test_refresh_desconocido_o_expirado_se_rechaza(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    assert refresh(client, "token-que-no-existe") == 401
    tokens = login(client)
    run_sql("UPDATE refresh_tokens SET expires_at = now() - interval '1 second'")
    assert refresh(client, tokens["refresh_token"]) == 401


def test_refresh_de_un_usuario_desactivado_se_rechaza(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    tokens = login(client)
    run_sql("UPDATE users SET is_active = false")
    assert refresh(client, tokens["refresh_token"]) == 401


def test_el_refresh_solo_se_guarda_como_hash(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    tokens = login(client)
    stored = run_sql("SELECT token_hash FROM refresh_tokens")
    assert stored and tokens["refresh_token"] not in str(stored)
    assert len(stored[0][0]) == 64


# --- logout ---------------------------------------------------------------------------------


def test_logout_revoca_el_refresh_y_es_idempotente(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    tokens = login(client)
    body = {"refresh_token": tokens["refresh_token"]}
    assert client.post("/api/v1/auth/logout", json=body, headers=bearer(tokens)).status_code == 204
    assert refresh(client, tokens["refresh_token"]) == 401
    assert client.post("/api/v1/auth/logout", json=body, headers=bearer(tokens)).status_code == 204
    assert "logout" in audit_actions()


def test_logout_no_revoca_tokens_de_otro_usuario(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user("a@example.com")
    make_user("b@example.com")
    alice, bob = login(client, "a@example.com"), login(client, "b@example.com")
    client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": bob["refresh_token"]},
        headers=bearer(alice),
    )
    assert refresh(client, bob["refresh_token"]) == 200


def test_logout_exige_sesion(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout", json={"refresh_token": "x"})
    assert response.status_code == 401


# --- cambio de contraseña ----------------------------------------------------------------------


def change(client: TestClient, tokens: dict[str, str], current: str, new: str) -> int:
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": current, "new_password": new},
        headers=bearer(tokens),
    )
    return int(response.status_code)


def test_cambiar_contrasena_cierra_las_demas_sesiones(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    other_session, current = login(client), login(client)
    assert change(client, current, DEFAULT_PASSWORD, "una-contrasena-nueva-9") == 204
    assert refresh(client, other_session["refresh_token"]) == 401
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": DEFAULT_PASSWORD},
        ).status_code
        == 401
    )
    login(client, password="una-contrasena-nueva-9")
    assert "password_changed" in audit_actions()


def test_cambiar_contrasena_con_la_actual_incorrecta(
    client: TestClient, make_user: UserFactory
) -> None:
    make_user()
    tokens = login(client)
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "no-es-la-actual", "new_password": "una-contrasena-nueva-9"},
        headers=bearer(tokens),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "wrong_current_password"


def test_cambiar_contrasena_valida_la_politica(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    tokens = login(client)
    assert change(client, tokens, DEFAULT_PASSWORD, "corta") == 422
    assert change(client, tokens, DEFAULT_PASSWORD, DEFAULT_PASSWORD) == 422
    assert change(client, tokens, DEFAULT_PASSWORD, "admin@example.com") == 422


def test_las_contrasenas_se_guardan_con_argon2(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    stored = run_sql("SELECT password_hash FROM users")[0][0]
    assert stored.startswith("$argon2id$")
    assert DEFAULT_PASSWORD not in stored


def test_el_refresh_dura_siete_dias(client: TestClient, make_user: UserFactory) -> None:
    make_user()
    login(client)
    expires = run_sql("SELECT expires_at - created_at FROM refresh_tokens")[0][0]
    assert timedelta(days=6, hours=23) < expires <= timedelta(days=7, seconds=5)


def test_login_actualiza_un_hash_con_parametros_antiguos(
    client: TestClient, make_user: UserFactory
) -> None:
    from argon2 import PasswordHasher

    make_user()
    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(DEFAULT_PASSWORD)
    run_sql("UPDATE users SET password_hash = :hash", hash=weak)
    login(client)
    upgraded = run_sql("SELECT password_hash FROM users")[0][0]
    assert upgraded != weak
    assert not PasswordHasher().check_needs_rehash(upgraded)
    login(client)
