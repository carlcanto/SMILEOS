"""Piezas comunes de la capa de dominio y aplicación (sin FastAPI ni SQL)."""

from dataclasses import dataclass


class DomainError(Exception):
    """Error de negocio con un código estable.

    La capa ``api`` lo traduce a una respuesta HTTP con ``STATUS_BY_CODE``; el dominio
    y los casos de uso no conocen HTTP.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class RequestContext:
    """Datos de la petición que se guardan en la auditoría."""

    ip: str | None = None
    request_id: str | None = None
