# --- Etapa 1: instala las dependencias en un entorno virtual ---
FROM python:3.13-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv
WORKDIR /srv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# --- Etapa 2: imagen final, sin herramientas de compilación ---
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/srv/.venv/bin:$PATH"
# Usuario sin privilegios; /srv/uploads es el volumen de imágenes (a partir de S5).
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /srv/uploads \
    && chown app:app /srv/uploads
WORKDIR /srv
COPY --from=builder /srv/.venv /srv/.venv
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
USER app
EXPOSE 8000
# api y worker usan esta misma imagen; el worker cambia el comando (python -m app.worker).
# Render inyecta PORT; en local se usa 8000.
CMD ["sh", "-c", "exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
