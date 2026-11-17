import json
import logging

from fastapi.testclient import TestClient

from app.main import create_app
from app.shared.config import Settings
from app.shared.logging import JsonFormatter


def build_client(settings: Settings) -> TestClient:
    app = create_app(settings)

    @app.get("/_t/items/{item_id}")
    async def item(item_id: int) -> dict[str, int]:
        return {"id": item_id}

    @app.get("/_t/boom")
    async def boom() -> None:
        raise RuntimeError("detalle-secreto")

    return TestClient(app, raise_server_exceptions=False)


def test_404_usa_el_formato_unico(unreachable_settings: Settings) -> None:
    with build_client(unreachable_settings) as client:
        response = client.get("/no-existe")
    body = response.json()
    assert response.status_code == 404
    assert body["error"]["code"] == "http_404"
    assert body["error"]["request_id"] == response.headers["x-request-id"]


def test_422_indica_donde_falla_sin_devolver_el_valor(unreachable_settings: Settings) -> None:
    with build_client(unreachable_settings) as client:
        response = client.get("/_t/items/dato-clinico-123")
    body = response.json()
    assert response.status_code == 422
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"][0]["loc"] == ["path", "item_id"]
    assert "dato-clinico-123" not in response.text


def test_500_no_filtra_detalles_internos(unreachable_settings: Settings) -> None:
    with build_client(unreachable_settings) as client:
        response = client.get("/_t/boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "detalle-secreto" not in response.text


def test_el_id_de_peticion_del_cliente_se_conserva(unreachable_settings: Settings) -> None:
    with build_client(unreachable_settings) as client:
        response = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers["x-request-id"] == "abc-123"


def test_el_log_de_acceso_no_incluye_parametros_de_consulta(
    unreachable_settings: Settings,
) -> None:
    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    with build_client(unreachable_settings) as client:
        logger = logging.getLogger("app.access")
        logger.addHandler(Capture())
        client.get("/health?documento=8-123-456")
    access = [r for r in records if r.getMessage() == "request"]
    assert access, "debe registrarse la petición"
    assert access[0].path == "/health"  # type: ignore[attr-defined]
    assert "8-123-456" not in json.dumps(access[0].__dict__, default=str)


def test_formato_json_de_los_logs() -> None:
    record = logging.LogRecord("app.x", logging.INFO, __file__, 1, "hola %s", ("mundo",), None)
    record.extra_dato = 7
    parsed = json.loads(JsonFormatter().format(record))
    assert parsed["message"] == "hola mundo"
    assert parsed["level"] == "INFO"
    assert parsed["extra_dato"] == 7
