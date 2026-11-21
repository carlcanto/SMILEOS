# ADR-0005 — El backend crea el esquema y el administrador inicial en cualquier base de Postgres

- Estado: aceptada (2026-11-21)
- Complementa: [ADR-0002](0002-perfiles-local-y-nube.md)

## Contexto

En la nube no hay una terminal para correr `alembic` ni el CLI, y la demostración debe poder
enlazarse a un proyecto de Supabase de cualquier cuenta (la del autor, la de su compañero o
la de un profesor) sin pasos manuales de base de datos. Supabase, además, puede exponer las
tablas del esquema `public` por su API de datos con una llave pública, y solo se conecta por
IPv6 en la conexión directa, que Render no alcanza.

## Decisión

- **El esquema lo crea el backend.** Con `RUN_MIGRATIONS_ON_START=true` la API aplica las
  migraciones de Alembic al arrancar. Apuntar `DATABASE_URL` a otra base vacía basta para
  que cree todo allí. El perfil local mantiene el comando explícito (`alembic upgrade head`
  o `python -m app.cli migrate`), que sigue siendo el valor por defecto.
- **Varias instancias a la vez son seguras**: las migraciones toman un candado de la base
  (`pg_advisory_xact_lock`), así que la segunda instancia espera y encuentra todo hecho.
- **Si la migración falla, la API no arranca** (falla rápido, con el error en los logs) en
  lugar de quedar a medias.
- **Administrador inicial por variables de entorno** (`BOOTSTRAP_ADMIN_EMAIL`, `_NAME` y
  `_PASSWORD`, las tres juntas): se crea solo si la base no tiene usuarios y nunca reemplaza
  a uno existente. Evita necesitar una terminal. La contraseña vive solo en el panel de Render.
- **La cadena de conexión se acepta tal como la entregan Supabase y otras herramientas**:
  `postgresql://` se convierte a `postgresql+asyncpg://`, `sslmode=` pasa a `ssl=`, se descarta
  `pgbouncer=true` y un host de Supabase usa `ssl=require` si no se indica otra cosa.
- **Solo el Session pooler de Supabase** (puerto 5432, IPv4). El *Transaction pooler*
  (puerto 6543) no admite sentencias preparadas y se rechaza al arrancar con un mensaje claro;
  la conexión directa (IPv6) no la alcanza Render.
- **RLS activado, sin políticas, en todas las tablas** (migración `0003`). El backend se
  conecta como dueño de las tablas, que ignora RLS; cualquier otro rol (como el de la API de
  datos de Supabase) no ve ninguna fila. Una prueba falla si una tabla nueva no lo activa.
  Esto no contradice la regla de no usar Supabase Auth ni RLS con políticas: aquí es solo una
  defensa por defecto, no lógica de negocio.

## Consecuencias

- Enlazar otra cuenta de Supabase son dos pasos: crear el proyecto y cambiar `DATABASE_URL`.
- El proyecto de Supabase debe estar vacío; si tiene tablas con los mismos nombres, la
  migración falla y el servicio no arranca.
- Cada migración futura que cree una tabla debe activar RLS (la prueba lo exige).
- Aplicar migraciones desde la API es cómodo para una demostración y riesgoso en producción
  con datos reales; por eso solo se activa con la variable y no en el perfil local.
- Si Supabase pausa el proyecto por inactividad, la API no arranca hasta que se restaure.
- Quedan fuera de esta decisión el almacenamiento de imágenes en Supabase Storage (S5) y la
  copia de datos entre proyectos.
