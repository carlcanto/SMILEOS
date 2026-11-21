"""Formato único de error: ``{"error": {"code", "message", "request_id"}}``."""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.domain import DomainError

logger = logging.getLogger("app.errors")

# Estado HTTP de cada código de error de negocio; un código desconocido es un 400.
STATUS_BY_CODE: dict[str, int] = {
    "not_authenticated": 401,
    "invalid_token": 401,
    "invalid_credentials": 401,
    "forbidden": 403,
    "user_not_found": 404,
    "email_already_exists": 409,
    "last_admin": 409,
    "self_deactivation": 409,
    "weak_password": 422,
    "wrong_current_password": 422,
}


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or uuid.uuid4().hex


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, object]] | None = None,
) -> JSONResponse:
    error: dict[str, object] = {
        "code": code,
        "message": message,
        "request_id": _request_id(request),
    }
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return error_response(request, exc.status_code, f"http_{exc.status_code}", str(exc.detail))

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status_code = STATUS_BY_CODE.get(exc.code, 400)
        response = error_response(request, status_code, exc.code, exc.message)
        if status_code == 401:
            response.headers["WWW-Authenticate"] = "Bearer"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Se devuelve dónde y qué falló, nunca el valor recibido (puede ser un dato clínico).
        details = [
            {"loc": [str(part) for part in err["loc"]], "type": err["type"], "msg": err["msg"]}
            for err in exc.errors()
        ]
        return error_response(
            request, 422, "validation_error", "Los datos enviados no son válidos.", details
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"path": request.url.path})
        return error_response(request, 500, "internal_error", "Error interno del servidor.")
