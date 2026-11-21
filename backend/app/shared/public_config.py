"""Configuración pública: lo que el frontend necesita saber antes de iniciar sesión."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.shared.config import Settings

router = APIRouter(prefix="/api/v1/config", tags=["system"])


class Features(BaseModel):
    patient_portal: bool


class PublicConfig(BaseModel):
    profile: Literal["local", "cloud"]
    features: Features


@router.get("/public")
async def public_config(request: Request) -> PublicConfig:
    settings: Settings = request.app.state.settings
    return PublicConfig(
        profile=settings.app_profile,
        features=Features(patient_portal=settings.feature_patient_portal),
    )
