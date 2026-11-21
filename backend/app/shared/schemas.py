"""Esquemas de la API compartidos por todos los módulos."""

from pydantic import BaseModel


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    per_page: int
