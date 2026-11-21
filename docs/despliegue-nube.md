# Despliegue en la nube (presentación de la tesis)

Tres servicios gratuitos, cada uno con una sola tarea, y **ningún paso manual de base de
datos**: el backend crea las tablas y el administrador inicial por sí solo en cualquier
proyecto de Supabase, de cualquier cuenta.

| Servicio | Aloja | Plan |
| --- | --- | --- |
| [Supabase](https://supabase.com) | La base de datos (Postgres) | Free |
| [Vercel](https://vercel.com) | El frontend | Hobby (uso no comercial) |
| [Render](https://render.com) | El backend (imagen Docker) | Free |

Solo con **datos ficticios**: los datos reales de la clínica nunca van a la nube
([ADR-0002](adr/0002-perfiles-local-y-nube.md)). La decisión de cómo el backend crea el
esquema está en el [ADR-0005](adr/0005-esquema-y-administrador-inicial-en-cualquier-supabase.md).

Los nombres exactos de botones y menús pueden variar un poco con el tiempo; los datos que se
copian y pegan (la URI, las variables) no.

## Orden

1. Supabase (la base) → 2. Vercel (el frontend, para conocer su URL) → 3. Render (el backend)
→ 4. Verificar.

---

## 1. Supabase

1. Entrar a supabase.com e iniciar sesión (con GitHub sirve).
2. **New project**: organización personal, nombre `smileos`, región cercana a donde vaya el
   backend (si Render va en *Virginia (US East)*, elegir *East US (North Virginia)*).
3. **Database password**: generar una y guardarla. Lo más simple es una de solo letras y
   números (`openssl rand -hex 16`); si tiene caracteres como `@ # / ?`, hay que escribirlos
   codificados en la URI (`@` = `%40`, `#` = `%23`, `/` = `%2F`, `?` = `%3F`).
4. Esperar a que el proyecto termine de crearse (unos minutos).
5. Botón **Connect** (arriba) → pestaña **Session pooler** → copiar la URI. Tiene esta forma:

   ```
   postgresql://postgres.<ref-del-proyecto>:[YOUR-PASSWORD]@<host>.pooler.supabase.com:5432/postgres
   ```

   Reemplazar `[YOUR-PASSWORD]` por la contraseña del paso 3 (sin los corchetes). **Guardar
   esta URI completa**: es el valor de `DATABASE_URL` en Render.

   | Opción de Connect | ¿Sirve? |
   | --- | --- |
   | **Session pooler** (puerto 5432) | **Sí.** Funciona sobre IPv4, que es lo que usa Render |
   | Direct connection | No: va por IPv6 y Render no la alcanza (suele salir como "Network is unreachable") |
   | Transaction pooler (puerto 6543) | No: no admite sentencias preparadas. El backend lo detecta y se niega a arrancar con un mensaje claro |

6. (Recomendado) Desactivar la **Data API** del proyecto (en la configuración del proyecto,
   sección *Data API* o *Integrations*): SmileOS no la usa. Además todas las tablas llevan
   RLS activado, así que aunque estuviera encendida no devolvería filas.

**No crear tablas ni ejecutar SQL.** El backend lo hace al arrancar.

---

## 2. Vercel (frontend)

1. Entrar a vercel.com e iniciar sesión con GitHub.
2. **Add New → Project** → importar el repositorio `carlcanto/SMILEOS` (dar a Vercel permiso
   para verlo si lo pide).
3. Antes de desplegar, configurar:

   | Campo | Valor |
   | --- | --- |
   | Framework Preset | Other |
   | Root Directory | `frontend` |
   | Install Command | `npm install` |
   | Build Command | `npm run build` |
   | Output Directory | `dist/spa` |

4. **Deploy**. Al terminar, copiar la URL (`https://<proyecto>.vercel.app`).
5. En *Settings → Git*, poner **Production Branch** = `cc/dev` mientras dure el desarrollo
   (para la presentación se cambia a `main`).

El frontend usa el router en modo `hash`, así que no necesita reglas de reescritura. Hoy
todavía no llama a la API (muestra datos de prueba); se verá igual hasta que se conecte.

---

## 3. Render (backend)

1. Entrar a render.com e iniciar sesión con GitHub.
2. **New → Web Service** → conectar el repositorio `carlcanto/SMILEOS`.
3. Configurar:

   | Campo | Valor |
   | --- | --- |
   | Name | `smileos-api` |
   | Language | Docker |
   | Branch | `cc/dev` |
   | Region | La misma zona que Supabase (p. ej. Virginia) |
   | Root Directory | (vacío) |
   | Dockerfile Path | `./backend/Dockerfile` |
   | Docker Build Context Directory | `./backend` |
   | Instance Type | Free |
   | Health Check Path | `/health/ready` |

   Los campos de Dockerfile, contexto y *Health Check Path* están en *Advanced*.

4. **Environment Variables** (en *Advanced*):

   | Variable | Valor |
   | --- | --- |
   | `APP_PROFILE` | `cloud` |
   | `DATABASE_URL` | La URI del Session pooler del paso 1.5, con la contraseña |
   | `JWT_SECRET` | Una cadena aleatoria de 64 caracteres: `openssl rand -hex 32` |
   | `RUN_MIGRATIONS_ON_START` | `true` |
   | `BOOTSTRAP_ADMIN_EMAIL` | El correo del primer administrador |
   | `BOOTSTRAP_ADMIN_NAME` | Su nombre completo |
   | `BOOTSTRAP_ADMIN_PASSWORD` | Su contraseña (mínimo 10 caracteres) |
   | `CORS_ORIGINS` | La URL de Vercel del paso 2.4, exacta: `https://<proyecto>.vercel.app` (sin barra final) |
   | `LOG_LEVEL` | `INFO` |

   No definir `PORT`: Render lo asigna solo.

5. **Create Web Service**. El primer despliegue tarda varios minutos. En los *Logs* deben
   aparecer, en este orden, `migrations_applied`, `bootstrap_admin_created` y `api_started`.

Los secretos (`DATABASE_URL`, `JWT_SECRET`, la contraseña del administrador) viven solo en
Render; nunca van al repositorio.

---

## 4. Verificar

Reemplazar `smileos-api` por el nombre real del servicio.

```bash
API=https://smileos-api.onrender.com

curl $API/health/ready
# {"status":"ok","database":"up","profile":"cloud"}

curl $API/api/v1/config/public
# {"profile":"cloud","features":{"patient_portal":false}}

curl -X POST $API/api/v1/auth/login -H 'content-type: application/json' \
  -d '{"email":"EL_CORREO","password":"LA_CONTRASEÑA"}'
# devuelve access_token, refresh_token y el usuario con rol admin
```

- En Supabase, *Table Editor* debe mostrar `users`, `roles`, `user_roles`, `refresh_tokens`,
  `audit_log` y `alembic_version`, creadas por el backend.
- `https://smileos-api.onrender.com/docs` muestra la documentación interactiva de la API.
- La primera petición tras un rato sin uso tarda cerca de un minuto: el plan gratis de Render
  duerme el servicio tras 15 minutos sin tráfico.

### Después del primer inicio de sesión

Borrar las tres variables `BOOTSTRAP_ADMIN_*` de Render. No es obligatorio (solo actúan si la
base no tiene usuarios y nunca reemplazan a uno existente), pero evita dejar una contraseña
guardada sin necesidad.

### Evitar que el servicio se duerma durante la presentación

Un monitor externo gratuito (UptimeRobot, cron-job.org) que pida `https://<api>/health` cada
10 minutos o menos. Conviene abrir la API un par de minutos antes de presentar.

---

## Cambiar a otra cuenta o proyecto de Supabase

Para enlazar otro proyecto (de la misma cuenta o de otra):

1. Crear el proyecto en Supabase y copiar su URI del **Session pooler** (paso 1).
2. En Render, cambiar `DATABASE_URL` y guardar: el servicio se redespliega solo.
3. El backend detecta la base vacía y crea las tablas, los roles y, si las variables
   `BOOTSTRAP_ADMIN_*` siguen definidas, el administrador.

Condiciones:

- **El proyecto debe estar vacío** (recién creado). Si ya tuviera tablas con los mismos
  nombres (`users`, `roles`...), la migración falla y el servicio no arranca.
- Los datos de la base anterior **no se trasladan**. Si hiciera falta, se copian con `pg_dump`.
- Para la demostración los datos son ficticios, así que normalmente basta empezar de cero.

---

## Si algo falla

Los mensajes están en *Logs* del servicio en Render.

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `Network is unreachable` o tiempo de espera al conectar | Se usó la *Direct connection* (IPv6) | Usar la URI del **Session pooler** |
| `Transaction pooler de Supabase (puerto 6543)` | La URI usa el puerto 6543 | Copiar la URI de *Session pooler* (puerto 5432) |
| `password authentication failed` | Contraseña equivocada o con caracteres especiales sin codificar | Regenerar la contraseña en Supabase (*Project Settings → Database*) y usar solo letras y números |
| `JWT_SECRET debe tener al menos 32 caracteres` | Falta o es corto | Generar uno con `openssl rand -hex 32` |
| `se definen las tres juntas o ninguna` | Falta alguna variable `BOOTSTRAP_ADMIN_*` | Definir las tres o borrar las tres |
| `relation "users" already exists` | El proyecto de Supabase no estaba vacío | Usar un proyecto nuevo |
| En el navegador: error de CORS | `CORS_ORIGINS` no coincide con la URL de Vercel | Debe ser el origen exacto: `https://`, sin barra final ni ruta |
| Login responde 401 y el administrador no existe | La base ya tenía usuarios, así que no se creó el inicial | Usar un proyecto de Supabase vacío (el restablecimiento de contraseña aún no existe) |
| Todo tarda ~1 minuto | El servicio estaba dormido (plan gratis) | Esperar; usar el monitor de la sección anterior |
| El servicio no se conecta tras unos días | Supabase pausa los proyectos gratis tras una semana sin actividad | *Restore project* en el panel de Supabase y reiniciar el servicio en Render |

## Referencias

- [Supabase: conexiones a la base de datos](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Supabase: compatibilidad IPv4 e IPv6](https://supabase.com/docs/guides/troubleshooting/supabase--your-network-ipv4-and-ipv6-compatibility-cHe3BP)
- [Supabase: proteger la API de datos (RLS)](https://supabase.com/docs/guides/api/securing-your-api)
- [Render: servicios web](https://render.com/docs/web-services) y [plan gratis](https://render.com/docs/free)
- [Quasar: desplegar una SPA](https://quasar.dev/quasar-cli-vite/developing-spa/deploying)
- [Vercel: monorepos](https://vercel.com/docs/monorepos)
