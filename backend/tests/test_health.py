from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.config import Settings
from tests.conftest import requires_database


def test_health_responde_sin_tocar_la_base(unreachable_settings: Settings) -> None:
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_devuelve_503_si_la_base_no_responde(unreachable_settings: Settings) -> None:
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "down", "profile": "local"}


@requires_database
def test_ready_devuelve_200_con_base_real(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up", "profile": "local"}


def test_ready_informa_el_perfil(unreachable_settings: Settings) -> None:
    cloud = unreachable_settings.model_copy(update={"app_profile": "cloud"})
    with TestClient(create_app(cloud)) as client:
        assert client.get("/health/ready").json()["profile"] == "cloud"
