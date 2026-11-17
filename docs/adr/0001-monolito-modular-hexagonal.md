# ADR-0001 — Monolito modular con arquitectura hexagonal

- Estado: aceptada (2026-11-17)
- Reemplaza: el objetivo del anteproyecto que hablaba de "microservicios"

## Contexto

SmileOS es el sistema de gestión de una sola clínica odontológica. Lo construyen dos
personas en un plazo acotado, y debe correr en una única computadora dentro de la
clínica (perfil local) y, para la presentación de la tesis, en servicios gratuitos de
la nube (perfil nube).

## Opciones consideradas

| Opción | A favor | En contra |
| --- | --- | --- |
| Microservicios completos | Escalan y se despliegan por separado | Red entre servicios, trazas distribuidas, consistencia entre bases, varios despliegues; todo eso para una clínica y dos desarrolladores |
| Monolito en capas tradicional | Lo más simple | Las reglas de negocio terminan mezcladas con FastAPI y SQL; difícil probar y difícil cambiar de almacenamiento |
| **Monolito modular hexagonal** | Un solo despliegue; módulos con fronteras claras; el dominio no depende de frameworks | Exige disciplina para respetar las fronteras |

## Decisión

Un único backend (FastAPI) organizado en módulos de negocio (`identity`, `patients`,
`agenda`, `records`, `imaging`, `billing`, `notifications`, `audit`, `inventory`).
Cada módulo tiene cuatro capas:

- `domain`: entidades y reglas, sin FastAPI ni SQL.
- `application`: casos de uso y puertos (interfaces).
- `infrastructure`: adaptadores (repositorios SQLAlchemy, almacenamiento, correo).
- `api`: routers y esquemas Pydantic.

Un módulo solo usa a otro a través de su capa `application`. Los procesos que corren
son `api` y `worker`, ambos desde la misma imagen.

## Consecuencias

- Un solo contrato (OpenAPI), una sola base de datos y un solo despliegue por perfil.
- Los puertos (`FileStorage`, `NotificationChannel`) permiten cambiar entre perfil
  local y nube sin tocar el negocio (ver ADR-0002).
- Si más adelante hiciera falta, un módulo puede extraerse a un servicio propio porque
  ya solo se comunica por su capa `application`.
- Se reconsidera esta decisión si cambian la escala (varias clínicas) o el tamaño del equipo.
