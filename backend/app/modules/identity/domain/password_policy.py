from app.shared.domain import DomainError

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password(password: str, *, email: str | None = None) -> None:
    """Política mínima: largo suficiente y que no sea el propio correo.

    Sin reglas de composición (mayúsculas, símbolos): el largo aporta más seguridad.
    La política definitiva se acuerda con la clínica **[POR CONFIRMAR]**.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise DomainError(
            "weak_password",
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres.",
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise DomainError(
            "weak_password",
            f"La contraseña no puede superar los {MAX_PASSWORD_LENGTH} caracteres.",
        )
    if not password.strip():
        raise DomainError("weak_password", "La contraseña no puede estar vacía.")
    if email is not None and password.lower() == normalize_email(email):
        raise DomainError("weak_password", "La contraseña no puede ser igual al correo.")
