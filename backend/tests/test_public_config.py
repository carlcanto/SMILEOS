from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.config import Settings


def test_config_publica_por_defecto(unreachable_settings: Settings) -> None:
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get("/api/v1/config/public")
    assert response.status_code == 200
    assert response.json() == {"profile": "local", "features": {"patient_portal": False}}


def test_config_publica_refleja_el_perfil_y_las_funciones(
    unreachable_settings: Settings,
) -> None:
    cloud = unreachable_settings.model_copy(
        update={"app_profile": "cloud", "feature_patient_portal": True}
    )
    with TestClient(create_app(cloud)) as client:
        body = client.get("/api/v1/config/public").json()
    assert body == {"profile": "cloud", "features": {"patient_portal": True}}


def test_config_publica_no_expone_secretos(unreachable_settings: Settings) -> None:
    with TestClient(create_app(unreachable_settings)) as client:
        text = client.get("/api/v1/config/public").text
    assert "jwt" not in text.lower()
    assert "database" not in text.lower()
