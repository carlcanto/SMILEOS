import pytest

from app.modules.identity.domain.password_policy import normalize_email, validate_password
from app.shared.domain import DomainError


def test_contrasena_valida_no_lanza_error() -> None:
    validate_password("una-contrasena-larga", email="a@example.com")


@pytest.mark.parametrize("password", ["", "corta", "123456789"])
def test_contrasena_corta_se_rechaza(password: str) -> None:
    with pytest.raises(DomainError) as error:
        validate_password(password)
    assert error.value.code == "weak_password"


def test_contrasena_demasiado_larga_se_rechaza() -> None:
    with pytest.raises(DomainError) as error:
        validate_password("a" * 129)
    assert error.value.code == "weak_password"


def test_contrasena_de_solo_espacios_se_rechaza() -> None:
    with pytest.raises(DomainError):
        validate_password(" " * 12)


def test_contrasena_igual_al_correo_se_rechaza() -> None:
    with pytest.raises(DomainError) as error:
        validate_password("Usuario@Example.com", email="usuario@example.com")
    assert "correo" in error.value.message


def test_el_correo_se_normaliza() -> None:
    assert normalize_email("  Admin@Clinica.LOCAL ") == "admin@clinica.local"
