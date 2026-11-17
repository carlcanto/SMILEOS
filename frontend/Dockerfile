# Contexto de construcción: la raíz del repositorio (ver deploy/docker-compose.local.yml).

# --- Etapa 1: compila la web de Quasar ---
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
# Sin scripts: el postinstall (quasar prepare) necesita quasar.config.js, que aún no está copiado.
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Etapa 2: nginx sirve lo compilado y reenvía /api a la API ---
FROM nginx:1.27-alpine
COPY deploy/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/spa /usr/share/nginx/html
EXPOSE 80
