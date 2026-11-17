# SmileOS

Sistema de gestión para la Clínica Odontológica del CRUV (Universidad de Panamá). Es el
proyecto de tesis de dos autores: el backend y la base de datos (Carlos Canto) y el
frontend (Virgilio Díaz de León). Monolito modular con arquitectura hexagonal; el mismo
código corre en dos perfiles: **local** (una computadora en la clínica) y **nube**
(presentación de la tesis: Vercel, Render y Supabase, solo con datos ficticios).

Contexto completo: `README.md`, `docs/adr/` (decisiones), `docs/sprints/` (bitácora por
sprint) y el documento de la tesis:
https://claude.ai/artifact/FfctBmqCTqHycG4eZzWmPc

## Reglas de trabajo (obligatorias)

- **Commits**: autor y firmante son `Carlos Canto <carloscanto04@gmail.com>`. Sin trailers
  `Co-Authored-By` ni `Claude-Session`, sin mencionar a Claude ni ninguna firma en commits,
  descripciones de pull request o código.
- **Ramas**: `main` es la estable y no se toca. Se trabaja en `cc/dev`; cada función sale
  de ella en una rama `cc/feat-<módulo>` y vuelve por pull request.
- **Antes de cada commit**, desde `backend/`: `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run mypy app tests` y `uv run pytest`
  (cobertura mínima 80 %). Desde `frontend/`: `npm run lint`.
- **Documentación**: una decisión de arquitectura nueva lleva un ADR en `docs/adr/`; al
  cerrar un sprint se agrega su entrada en `docs/sprints/` con los siete puntos de la
  plantilla (objetivo, decisiones, cambios, pruebas, problemas y soluciones, evidencia,
  pendientes) y se refleja en el documento de la tesis.
- **No inventar**: lo que no está confirmado se marca **[POR CONFIRMAR]**. No citar
  fuentes bibliográficas que no se hayan verificado.
- **Redacción de la tesis**: forma impersonal.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `backend/` | API y worker (FastAPI, SQLAlchemy 2 asíncrono, asyncpg, Alembic, `uv`, Python 3.13) |
| `frontend/` | Web (Vue 3 + Quasar). Es trabajo del otro autor: no refactorizar sin acordarlo |
| `deploy/` | Docker Compose del perfil local, nginx y ejemplos de variables de entorno |
| `docs/` | `adr/`, `sprints/`, `campo/` (material de la clínica) |

Cuatro procesos (`frontend`, `api`, `worker`, `db`) a partir de tres imágenes; `api` y
`worker` usan la misma imagen con comandos distintos.

## Comandos

```bash
# Backend (desde backend/)
uv sync
uv run uvicorn app.main:create_app --factory --reload
uv run alembic upgrade head
TEST_DATABASE_URL=postgresql+asyncpg://smileos:smileos@127.0.0.1:5432/smileos_test uv run pytest --cov=app

# Perfil local completo (desde deploy/, con deploy/.env creado a partir de env/.env.local.example)
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml run --rm api alembic upgrade head
```

## Convenciones del backend

- Cada módulo de `backend/app/modules/<módulo>/` tiene cuatro capas: `domain` (reglas, sin
  FastAPI ni SQL), `application` (casos de uso y puertos), `infrastructure` (adaptadores) y
  `api` (routers y esquemas). Un módulo usa a otro solo a través de su capa `application`.
- Lo que cambia entre perfiles va detrás de puertos con un adaptador por perfil
  (`FileStorage`, `NotificationChannel`). El código no tiene ramas por perfil: todo sale de
  variables de entorno (`app/shared/config.py`).
- Supabase se usa solo como Postgres y almacenamiento. No usar Supabase Auth ni RLS: no
  existen en el perfil local. SQL estándar de Postgres.
- Reglas que no pueden fallar se imponen en la base de datos (restricciones, secuencias,
  llaves únicas), no solo en el código. Un caso de uso decide cuándo hacer `commit`; los
  ayudantes no lo hacen por su cuenta.
- La cola de notificaciones es la tabla `notification_outbox` (sin Redis ni Celery),
  escrita en la misma transacción que la acción que la origina.
- Un único formato de error: `{"error": {"code", "message", "request_id"}}`. Los errores 422
  indican dónde falló, nunca el valor recibido.
- **Privacidad**: nada de datos clínicos ni personales en logs, mensajes de error ni
  parámetros de consulta registrados. Las pruebas y la nube usan datos ficticios.
- Las migraciones se aplican con comando explícito, no al arrancar la API.

## Estado

S0 (fundaciones) completo en local. Siguiente: S1 (identidad: JWT propio con Argon2,
roles `admin`, `odontologo` y `recepcion`, auditoría). Pendientes abiertos: despliegue en
la nube, confirmar con el autor del frontend el JWT propio y el enum de estados de cita, y
la lista de **[POR CONFIRMAR]** del documento de la tesis.
