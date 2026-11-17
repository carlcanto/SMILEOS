# ADR-0003 — La cola de notificaciones vive en Postgres (outbox), sin Redis ni Celery

- Estado: aceptada (2026-11-17)

## Contexto

Los recordatorios de citas deben salir sin que el usuario espere, sobrevivir a reinicios
y apagones, y reintentarse cuando no hay internet. El sistema corre en una sola
computadora en la clínica.

## Opciones consideradas

| Opción | A favor | En contra |
| --- | --- | --- |
| Celery + Redis | Estándar para colas de trabajo | Dos servicios más que instalar, vigilar y respaldar |
| Tareas en la propia API (APScheduler o BackgroundTasks) | Cero infraestructura | Se pierden al reiniciar la API; se duplican si hay varias instancias |
| **Tabla `notification_outbox` + proceso `worker`** | La cola se guarda en la misma transacción que la cita; no hay infraestructura nueva | Hay que implementar reintentos y bloqueo de filas (se hace con `FOR UPDATE SKIP LOCKED`) |

## Decisión

La API inserta una fila en `notification_outbox` dentro de la misma transacción que la
acción que la origina. El proceso `worker` (misma imagen que la API, otro comando) lee
las filas pendientes, las envía por cada canal y las marca como enviadas; si falla, las
reintenta con espera creciente. Estados: `pending`, `sent`, `failed`, `dead`.

## Consecuencias

- No se pierde ningún mensaje por un corte de luz ni por falta de internet.
- No hay Redis que administrar en la clínica.
- Las alertas en pantalla funcionan sin internet; correo y WhatsApp salen al volver la conexión.
- Si el volumen creciera mucho, la cola puede moverse a un broker sin cambiar la API.

El esqueleto del `worker` se creó en S0 (arranca, comprueba la base y se detiene de forma
ordenada). La lógica de la cola llega en S3 (escritura) y S7 (envío).
