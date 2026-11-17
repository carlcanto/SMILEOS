# SmileOS

Sistema de gestión para la Clínica Odontológica del Centro Regional Universitario de
Veraguas (CRUV). Proyecto de tesis de la Escuela de Ingeniería en Informática,
Universidad de Panamá.

Monolito modular con arquitectura hexagonal. El mismo código corre en dos perfiles:
**local** (una computadora dentro de la clínica) y **nube** (presentación de la tesis).

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `frontend/` | Web (Vue 3 + Quasar) |
| `backend/` | API y worker (FastAPI, SQLAlchemy, Alembic) |
| `deploy/` | Docker Compose, nginx y ejemplos de variables de entorno |
| `docs/` | Decisiones de arquitectura (`adr/`), bitácora por sprint (`sprints/`) y material de campo (`campo/`) |

## Arranque rápido (perfil local, con Docker)

```bash
cd deploy
cp env/.env.local.example .env        # y cambiar POSTGRES_PASSWORD
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml run --rm api alembic upgrade head
```

Abrir `http://localhost` (o el `HTTP_PORT` elegido). Comprobar la salud con
`http://localhost/api/health/ready`.

## Desarrollo del backend (sin Docker)

Requiere Python 3.13, [uv](https://docs.astral.sh/uv/) y un Postgres.

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --reload
```

Pruebas y calidad (`TEST_DATABASE_URL` apunta a una base de pruebas):

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy app tests
TEST_DATABASE_URL=postgresql+asyncpg://smileos:smileos@127.0.0.1:5432/smileos_test uv run pytest --cov=app
```

## Desarrollo del frontend

```bash
cd frontend
npm install
npx quasar dev
```

Usuario de prueba del login provisional: `admin` / `admin`.

## Documentación

- [ADR-0001 Monolito modular hexagonal](docs/adr/0001-monolito-modular-hexagonal.md)
- [ADR-0002 Perfiles local y nube](docs/adr/0002-perfiles-local-y-nube.md)
- [ADR-0003 Cola en Postgres, sin Redis](docs/adr/0003-postgres-como-cola-sin-redis.md)
- [Bitácora S0](docs/sprints/S0.md)

## Ramas

`main` es la rama estable; `cc/dev` es la base de integración del backend y de ella salen
las ramas de cada función.
