from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.config import Settings


def test_origen_permitido_recibe_cabecera_cors(unreachable_settings: Settings) -> None:
    configured = unreachable_settings.model_copy(
        update={"cors_origins": ["https://smileos.vercel.app"]}
    )
    with TestClient(create_app(configured)) as client:
        response = client.get("/health", headers={"Origin": "https://smileos.vercel.app"})
    assert response.headers["access-control-allow-origin"] == "https://smileos.vercel.app"


def test_origen_no_listado_no_recibe_cabecera_cors(unreachable_settings: Settings) -> None:
    configured = unreachable_settings.model_copy(
        update={"cors_origins": ["https://smileos.vercel.app"]}
    )
    with TestClient(create_app(configured)) as client:
        response = client.get("/health", headers={"Origin": "https://otro.example.com"})
    assert "access-control-allow-origin" not in response.headers


def test_sin_origenes_configurados_cors_esta_apagado(unreachable_settings: Settings) -> None:
    with TestClient(create_app(unreachable_settings)) as client:
        response = client.get("/health", headers={"Origin": "https://smileos.vercel.app"})
    assert "access-control-allow-origin" not in response.headers
