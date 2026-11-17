# ADR-0002 — Dos perfiles (local y nube) con el mismo código y las mismas imágenes

- Estado: aceptada (2026-11-17)

## Contexto

La clínica no puede garantizar una conexión estable a internet, así que operará con el
sistema instalado en una computadora dentro del edificio. La tesis, en cambio, se
presenta con el sistema en la nube. Se quiere demostrar que es el mismo software.

## Decisión

- El perfil se elige solo con variables de entorno (`APP_PROFILE`, `DATABASE_URL`,
  `STORAGE_BACKEND`, `CORS_ORIGINS`...). El código no tiene ramas por perfil.
- Las imágenes Docker son las mismas en ambos perfiles.
- Supabase se usa únicamente como Postgres y almacenamiento de archivos. No se usa
  Supabase Auth ni políticas RLS, porque no existen en el perfil local.
- Lo que cambia entre perfiles se aísla detrás de puertos con un adaptador por perfil:
  almacenamiento de archivos (`FileStorage`: disco local o Supabase Storage) y canales
  de notificación (`NotificationChannel`: alerta en pantalla, correo, WhatsApp).
- La URL de conexión acepta el formato de Supabase (`postgresql://`) y se convierte sola
  al driver asíncrono.

| Pieza | Perfil local (clínica) | Perfil nube (presentación) |
| --- | --- | --- |
| Frontend | Contenedor nginx | Vercel |
| API | Contenedor `api` | Render (Docker) |
| Worker | Contenedor `worker` | Render si el plan lo permite, o dentro de la API en la demo |
| Base de datos | Contenedor Postgres | Supabase |
| Archivos | Disco local (volumen) | Supabase Storage |
| Datos | Reales | Ficticios |

## Consecuencias

- La portabilidad se puede medir: la misma suite de pruebas debe pasar contra Postgres
  local y contra Supabase.
- Hay que evitar funciones propias de Supabase y limitarse a SQL estándar de Postgres.
- La misma versión mayor de Postgres debe usarse en ambos perfiles (por confirmar).
