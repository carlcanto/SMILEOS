# ADR-0004 — Autenticación propia: acceso JWT corto, refresco opaco rotativo y Argon2id

- Estado: aceptada (2026-11-21); el uso de JWT propio queda **[POR CONFIRMAR]** con el autor del frontend
- Complementa: [ADR-0002](0002-perfiles-local-y-nube.md) (sin Supabase Auth)

## Contexto

El sistema guarda datos clínicos y corre en dos perfiles. En el perfil local no existe
Supabase, así que la autenticación no puede depender de él. Hay tres roles fijos
(`admin`, `odontologo`, `recepcion`) y un usuario puede tener más de uno.

## Opciones consideradas

| Opción | A favor | En contra |
| --- | --- | --- |
| Supabase Auth | Ya resuelto | No existe en el perfil local; contradice ADR-0002 |
| Sesiones con cookie en el servidor | Revocación inmediata y simple | Exige configurar cookies y CSRF entre Vercel y Render en la nube |
| **Token de acceso JWT corto + token de refresco opaco** | Funciona igual en los dos perfiles; el frontend usa una cabecera estándar | Hay que implementar la rotación y la revocación |

## Decisión

- **Acceso**: JWT firmado con HS256, vida de 15 minutos (`ACCESS_TOKEN_MINUTES`). Solo lleva
  el identificador del usuario. Los roles y el estado activo **se leen de la base en cada
  petición**: desactivar a un usuario o cambiarle los roles aplica de inmediato, aunque su
  token siga vigente. El costo es una lectura por petición, irrelevante a la escala de una clínica.
- **Refresco**: cadena aleatoria opaca de 48 bytes, vigente 7 días (`REFRESH_TOKEN_DAYS`). En
  la base solo se guarda su SHA-256, así que una filtración de la tabla no sirve para
  iniciar sesión. Se **rota** en cada uso. Si un token ya usado vuelve a presentarse (señal
  de posible robo) se revocan todas las sesiones del usuario y se audita el evento.
- **Contraseñas**: Argon2id con los parámetros por defecto de `argon2-cffi`; se recalculan al
  iniciar sesión si los parámetros cambian. Mínimo 10 caracteres, máximo 128, sin reglas de
  composición. Un correo inexistente tarda lo mismo que una contraseña errónea y la
  respuesta es idéntica, para no revelar qué correos existen.
- **Roles**: tabla `roles` con el código como llave y relación muchos a muchos con los
  usuarios (`user_roles`).
- **Auditoría**: inicios de sesión (exitosos y fallidos), cierre de sesión, reuso de token,
  cambios de contraseña y toda gestión de usuarios quedan en `audit_log`, sin contraseñas
  ni tokens.
- **Protecciones de administración**: nadie puede desactivarse a sí mismo y siempre debe
  quedar al menos un administrador activo (se comprueba bloqueando sus filas).
- El primer administrador se crea con `python -m app.cli create-admin`, con la contraseña
  por teclado o por `ADMIN_PASSWORD`; nunca hay una contraseña fija en el código.

## Consecuencias

- El frontend debe guardar los tokens, enviar `Authorization: Bearer` y renovar con
  `/api/v1/auth/refresh` al recibir un 401. Dónde guardarlos (memoria, `localStorage`) y el
  riesgo de XSS se deciden con el autor del frontend **[POR CONFIRMAR]**.
- Dos pestañas que renuevan a la vez con el mismo token pueden disparar la detección de
  reuso y cerrar la sesión; el frontend debe serializar la renovación.
- La limitación de intentos de inicio de sesión queda para el sprint de endurecimiento (S9).
- Detrás de nginx la IP registrada en la auditoría es la del proxy hasta configurar los
  encabezados de reenvío (S9).
