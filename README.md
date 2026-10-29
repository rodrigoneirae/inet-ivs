# inet-ivs

Proyecto Django preparado para ASGI, Channels, Celery, Redis y PostgreSQL. Docker Compose ejecuta Django y Channels en `web`, las tareas en `worker`, el planificador en `beat`, PostgreSQL en `db` y Redis en `redis`.

## Desarrollo web con Django y Astro

`frontend/` contiene la interfaz Astro estática que consulta la API de Django por el mismo origen. En el despliegue, Django entrega el HTML compilado en `/` y `/pedidos/` a través de sus rutas y middleware; la ruta de pedidos exige sesión y el permiso `anymarket.view_pedido`. Nginx sirve los recursos compilados `/_astro/` y reenvía las demás rutas a Django. Django Admin conserva sus propias plantillas en `/admin/`.

Por ahora el desarrollo se centra en Django y Astro. Para ejecutar Astro con Django en `127.0.0.1:8000`:

```bash
cd frontend
npm ci
npm run dev
```

Abre `http://127.0.0.1:4321/`. Astro mantiene ese puerto fijo y su proxy de desarrollo dirige `/api/` y `/static/` a Django. En este modo el servidor Astro atiende las páginas directamente para permitir recarga rápida: las verificaciones de permisos siguen aplicándose en la API Django. Para probar el middleware de página, compila Astro (`npm run build`) y ejecuta Django detrás de Nginx como en el despliegue. Para enviar formularios desde Astro, configura `DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:4321` en el entorno del proceso Django o en `.env.dev` y reinícialo. Si utilizas `localhost`, incluye también `http://localhost:4321`; `.env.dev.example` muestra ambos orígenes locales. Si usas Compose local, vuelve a crear el servicio web para que reciba las variables actualizadas. Redis e IVS SAT deben estar disponibles para el inicio de sesión. No expongas el servidor de desarrollo en producción.

`docker-compose.yml` incluye el servicio `frontend` construido con Nginx: sirve los recursos `/_astro/` y envía las páginas, API, administración y WebSockets a `web`. La imagen Django también compila Astro para entregar el HTML; ambas imágenes deben construirse del mismo commit y lockfile. Para validar la configuración ejecuta `docker compose -f docker-compose.yml config --quiet` con las variables del proyecto configuradas. En Dockploy usa ese archivo y dirige el dominio al puerto 8080 de `frontend`. El proxy exterior debe establecer HTTPS y sobrescribir `X-Forwarded-Proto`; el servicio no debe exponerse directamente. Prueba el enrutamiento y las sesiones en un entorno separado antes de cambiar un despliegue existente.

### Sistema de diseño

`frontend/src/styles/main.css` define el sistema de diseño con Tailwind CSS v4 mediante tokens `@theme` en OKLCH. La paleta base se organiza en cuatro familias: `brand` (índigo, acciones principales), `success` (verde), `warning` (ámbar) y `danger` (rojo). Sobre ellas se declaran los tokens semánticos que consume la interfaz: `canvas`, `surface`, `ink`, `line`, `primary` y sus equivalentes. Los tokens semánticos se redefinen dentro de `.dark`, de modo que los componentes no dependen de variantes `dark:` para superficies y texto.

Los componentes reutilizables se declaran en `@layer components` (`.btn`, `.field`, `.card`, `.chip`, `.nav-link`, `.toast`, entre otros) y las capas de terceros se alinean con la misma paleta: Tabulator usa las variables del tema para cabecera, filas y filtros, y Litepicker recibe sus variables `--litepicker-*` desde los tokens. El tema elegido y el estado del menú lateral se guardan en `localStorage`; en la primera visita se respeta `prefers-color-scheme`.

Al modificar la paleta, cambia los tokens de `@theme` y los valores de `.dark` en `main.css`, y verifica el resultado con `npm run build` en `frontend/`. Los iconos se declaran como símbolos SVG en `frontend/src/pages/index.astro` y se reutilizan con `<use href="#icon-...">`.

### Preparación para multiplataforma

La interfaz Astro se compila como archivos estáticos y usa rutas relativas `/api/`; Django conserva sesiones, CSRF, permisos y validación en el servidor. En el despliegue web, Nginx sirve ambos bajo el mismo origen. Estas decisiones mantienen la interfaz desacoplada de funciones nativas mientras se desarrolla y permiten evaluar su reutilización en futuros clientes.

`frontend/src-tauri/` es una base experimental. La configuración predeterminada apunta a `https://example.invalid`; para una prueba Linux con la interfaz remota, ejecuta desde `frontend/`:

```bash
source "$HOME/.cargo/env"
npm run tauri -- build --debug --no-bundle --config '{"app":{"windows":[{"title":"INET IVS","url":"https://inet-ivs.inversierra.cl/","width":1280,"height":800}]}}'
./src-tauri/target/debug/inet-ivs
```

Esta compilación Linux de depuración se ha verificado, pero la autenticación, cookies, CSRF, navegación y descargas aún deben probarse en la ventana Tauri. La URL de prueba se incluye en el ejecutable; no contiene credenciales. La aplicación depende de la disponibilidad del sitio remoto. Antes de distribuir en Linux, Windows, macOS, Android o iOS hay que validar cada plataforma y su proceso de empaquetado y firma; los proyectos móviles todavía deben generarse. iOS y macOS requieren macOS con Xcode. No es necesario instalar Rust ni las herramientas de Tauri para trabajar únicamente en la web.

Inicia Django, PostgreSQL, IVS SAT y Redis. La API utiliza Redis para limitar intentos de acceso; si hay varias instancias web deben compartir Redis. El límite usa `REMOTE_ADDR`: configura el proxy de modo que Django reciba la dirección correcta o aplica un límite equivalente en el proxy; de otro modo todos los clientes detrás del proxy compartirán el límite. Publica Django mediante HTTPS con certificado válido y configura `DJANGO_ALLOWED_HOSTS` para el dominio.

## Desarrollo local sin Docker

Activa el entorno virtual e instala las dependencias:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
uvicorn inet_ivs.asgi:application --host 127.0.0.1 --port 8000 --reload
```

Inicia también Astro como se explica arriba y abre `http://127.0.0.1:4321/` para iniciar sesión con un usuario de IVS SAT. Django Admin está disponible en `http://127.0.0.1:8000/admin/`.

### Usuarios y acceso

Configura la conexión `ivs_sat` y aplica las migraciones locales con `python manage.py migrate`. Para importar inicialmente los usuarios, ejecuta `python manage.py sincronizar_usuarios_ivs`. Celery Beat programa una sincronización cada hora; deben estar funcionando tanto Beat como el worker. El ingreso también consulta IVS SAT y sincroniza la cuenta inmediatamente, por lo que requiere que la base de origen esté disponible. Las contraseñas se guardan localmente como hashes de Django; en la base de origen permanecen como están.

Los registros sin contraseña, con nombres duplicados o que coincidan con una cuenta local no vinculada se omiten. Revisa y corrige estos casos en el sistema de origen antes de utilizarlos. La sincronización no borra cuentas locales; una cuenta eliminada del origen no puede iniciar sesión de nuevo. Las sesiones existentes no se cierran automáticamente cuando se elimina una cuenta del origen. El backend de acceso acepta únicamente usuarios de IVS SAT, también para `/admin/`: `createsuperuser` por sí solo no habilita el ingreso. Los permisos administrativos deben asignarse explícitamente a un usuario importado.

La base principal predeterminada es PostgreSQL `inet-ivs` en `192.168.0.8`. En desarrollo, Django carga las credenciales de `.env.dev` automáticamente; las variables de entorno ya definidas tienen prioridad. No se carga ese archivo cuando `DJANGO_DEBUG=False` está definido en el entorno. Redis debe estar ejecutándose en `localhost:6379` para la capa de Channels; comprueba su disponibilidad con `redis-cli ping`. Para utilizar otra dirección, define la variable `REDIS_URL` antes de iniciar Uvicorn.

## Conexiones a bases de datos

Configura las variables de entorno antes de iniciar cada proceso de Django, Uvicorn, Celery o Compose. `.env.example` contiene los nombres; guarda las credenciales reales únicamente en el entorno o en un archivo privado excluido de Git.

| Alias Django | Destino | Variables |
| --- | --- | --- |
| `default` | PostgreSQL de la aplicación, `192.168.0.8` | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| `ivs_sat` | PostgreSQL `IVS_SAT`, `192.168.0.8` | `IVS_SAT_USER`, `IVS_SAT_PASSWORD`; opcionalmente `IVS_SAT_DB`, `IVS_SAT_HOST`, `IVS_SAT_PORT` |
| `sqlserver` | SQL Server, `192.168.0.10` | `SQLSERVER_DB`, `SQLSERVER_USER`, `SQLSERVER_PASSWORD`; opcionalmente `SQLSERVER_HOST`, `SQLSERVER_PORT` |

Los puertos predeterminados son 5432 y 1433. Las conexiones secundarias se habilitan al definir `IVS_SAT_USER` y `SQLSERVER_DB`, respectivamente. La base principal usa por defecto `inet-ivs` en `192.168.0.8`; configura `POSTGRES_USER` y `POSTGRES_PASSWORD` y, si corresponde, cambia `POSTGRES_DB` y `POSTGRES_HOST`. El nombre `IVS_SAT` respeta mayúsculas. SQL Server utiliza `mssql-django` y `mssql-python`, que incluye el controlador ODBC 18; el servidor debe disponer de un certificado confiable válido para el host configurado. Consulta los requisitos de sistema de [mssql-python](https://github.com/microsoft/mssql-python#installation).

Consulta las bases secundarias explícitamente con `Modelo.objects.using('ivs_sat')` o `Modelo.objects.using('sqlserver')`, o mediante `django.db.connections` para SQL parametrizado. El router impide aplicar operaciones de migración de modelos en esos dos alias; no ejecutes `migrate --database` sobre ellos, ya que Django podría crear su tabla de registro de migraciones. Usa cuentas con los permisos mínimos necesarios. La cuenta de IVS SAT requiere lectura de `public.ivs_sysusuarios`.

En Compose, `POSTGRES_HOST` permite seleccionar el servidor externo; el servicio local `db` sigue existiendo y no contiene automáticamente los datos de ese servidor. **El servicio `web` ejecuta `migrate` automáticamente contra `default` al iniciar**: verifica nombre, permisos y respaldo antes de apuntarlo a una base existente. Cambiar de SQLite o del PostgreSQL local a otro servidor no transfiere datos.

Uvicorn ejecuta ASGI, necesario para WebSockets. Django `runserver` no utiliza el enrutador ASGI de Channels con esta configuración.

Para ejecutar tareas y tareas programadas, abre dos terminales adicionales, activa `.venv` en cada una y ejecuta:

```bash
celery -A inet_ivs worker --loglevel=info
```

```bash
celery -A inet_ivs beat --loglevel=info --schedule=celerybeat-schedule
```

Inicia solo una instancia de Beat para evitar duplicar tareas programadas. El archivo de agenda local está excluido de Git. El worker debe reiniciarse cuando cambia el código de tareas; Beat, cuando cambia su programación.

## Tareas y programación

### Pedidos AnyMarket

La integración consulta pedidos creados desde el 27-10-2026 a las 00:00 en `ANYMARKET_TIME_ZONE` (por defecto `America/Santiago`, horario de Chile continental). La carga inicial importa pedidos en estado `PAID_WAITING_SHIP`; las consultas incrementales incorporan los que alcancen ese estado y actualizan los ya importados, incluso si se cancelan. La consulta inicial no incluye pedidos que ya hayan avanzado a otro estado. Los datos completos se guardan en la base principal y todavía no se envían a INET. Define el acceso y la retención de esta base teniendo en cuenta que los pedidos contienen datos personales.

Configura `ANYMARKET_TOKEN` en el entorno privado, `ANYMARKET_ENVIRONMENT` como `sandbox` o `production` (predeterminado production) y `ANYMARKET_PLATFORM` con el nombre registrado ante AnyMarket. Activa la ejecución automática con `ANYMARKET_ENABLED=true` y reinicia worker y beat tras aplicar las migraciones. El planificador consulta cada minuto; requiere worker, beat y acceso a PostgreSQL y AnyMarket. El token debe estar disponible en el worker y no debe registrarse en logs.

La integración usa consultas paginadas y no marca el feed como leído. La primera ejecución recorre el historial en intervalos de hasta 119 días; las siguientes consultan cambios en intervalos de hasta 6 días, con un solapamiento de cinco minutos. Los pedidos se guardan en lotes de 100 mediante transacciones cortas; el punto de control avanza únicamente al completar cada intervalo, de modo que tras un fallo puede repetirse sin duplicar pedidos. Un bloqueo de sesión PostgreSQL evita que se solapen la sincronización y la reconciliación; requiere conexión directa o un pool con afinidad de sesión (no PgBouncer en modo transacción).

Con `ANYMARKET_ENABLED=true`, Beat también programa una reconciliación diaria a las 03:00 en `DJANGO_TIME_ZONE` (UTC por defecto), que vuelve a consultar actualizaciones de los últimos 7 días y actualiza los pedidos ya importados. Los pedidos no importados solo se incorporan si están actualmente en `PAID_WAITING_SHIP`. Si la reconciliación coincide con otro proceso, Celery la reintenta; supervisa los fallos y los límites de la API. La pantalla muestra la última ejecución correcta y el último error de ambos procesos. Una demora de indexación o interrupción superior a siete días requiere una recuperación adicional. Mantén una sola cuenta y ambiente por base de datos: cambiar token o ambiente requiere una estrategia de migración de datos y punto de control.

El listado está disponible en `/pedidos/` para usuarios con el permiso `anymarket.view_pedido`, que un administrador puede asignar directamente o mediante un grupo en Django Admin. El acceso se deniega por defecto. Astro usa Tabulator para la tabla y requiere JavaScript; las rutas antiguas `/login/` y `/anymarket/pedidos/` redirigen a las nuevas rutas. Las rutas antiguas de exportación y sincronización se conservan, además de las rutas de la API.

La columna Status corresponde al estado del marketplace. La exportación Excel incluye todos los pedidos que coinciden con los filtros, con un máximo de 50 000 por descarga; para instalar la dependencia de exportación, actualiza el entorno con `pip install -r requirements.txt` y reconstruye la imagen si usas Docker.

Los filtros de fecha usan Litepicker 2.0.12, servido localmente desde `static/vendor/litepicker/` bajo licencia MIT. Los campos aceptan fechas escritas como `AAAA-MM-DD` y conservan el selector de fecha nativo cuando JavaScript no está disponible. La validación y la zona horaria se aplican en el servidor.

Define tareas con `@shared_task` en `tasks.py` dentro de una aplicación de Django incluida en `INSTALLED_APPS`. Envíalas con `nombre_de_tarea.delay(...)`. Define la programación en `CELERY_BEAT_SCHEDULE` de `inet_ivs/settings.py`. Para configurar la zona horaria, usa `DJANGO_TIME_ZONE` (por defecto `UTC`).

Channels usa la base Redis 0, Celery usa la 1 como cola y la 2 para resultados. El Redis de Compose mantiene los datos en un volumen con AOF; esto no reemplaza los respaldos ni garantiza por sí solo la ejecución exacta de cada tarea. El planificador de Beat mantiene su estado en otro volumen y debe ejecutarse como una sola instancia. No hay administración de horarios desde Django Admin: el programador integrado usa la configuración del código.

## Desarrollo local con Docker

1. Copia `.env.dev.example` a `.env.dev` y reemplaza la clave y la contraseña por valores locales. Genera una clave con:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

2. Levanta Django con ASGI y recarga automática, PostgreSQL, Redis, Celery Worker y Beat:

   ```bash
   docker compose --env-file .env.dev -p inet-ivs-dev -f docker-compose.yml -f compose.local.yml up --build
   ```

3. Inicia Astro con `npm run dev` desde `frontend/` y abre `http://127.0.0.1:4321/`. Para importar los usuarios desde otra terminal:

   ```bash
   docker compose --env-file .env.dev -p inet-ivs-dev -f docker-compose.yml -f compose.local.yml exec web python manage.py sincronizar_usuarios_ivs
   ```

Los archivos se montan desde el equipo y Uvicorn recarga el código Python al cambiarlo. Si cambias `requirements.txt`, reconstruye con `up --build`. Para crear migraciones, usa el mismo comando `docker compose ... exec web python manage.py makemigrations`.

El usuario del contenedor es `1000:1000` por defecto para que las migraciones creadas sean editables en Linux. Si tu usuario tiene otro UID o GID, añade `LOCAL_UID` y `LOCAL_GID` a `.env.dev` con los valores de `id -u` e `id -g`.

Para detener el entorno sin borrar datos:

```bash
docker compose --env-file .env.dev -p inet-ivs-dev -f docker-compose.yml -f compose.local.yml down
```

La base se conserva en el volumen local del proyecto Compose. La base SQLite local existente no se importa automáticamente a PostgreSQL. El entorno local no expone PostgreSQL ni Redis fuera de la red Docker. El código de worker y beat también se monta localmente, pero debes reiniciar esos servicios al cambiar tareas o su programación.

## Dockploy

1. Sube el repositorio a GitHub sin `.env`, SQLite ni el entorno virtual.
2. Crea un servicio **Compose** en Dockploy y conecta el repositorio y la rama. Selecciona `docker-compose.yml`; no incluyas `compose.local.yml`.
3. Configura en las variables del servicio Compose los valores de `.env.example`. Usa una clave y contraseña nuevas, `DJANGO_DEBUG=False`, el dominio en `DJANGO_ALLOWED_HOSTS` y `https://tu-dominio` en `DJANGO_CSRF_TRUSTED_ORIGINS`.
4. Configura el dominio para el servicio `web` y su puerto interno `8000`. Si usas Cloudflare Tunnel con destino HTTP al proxy de Dockploy, configura el dominio HTTP en Dockploy y HTTPS en Cloudflare. Despliega y revisa los logs de `web`, `worker` y `beat`.
5. En la terminal del contenedor `web`, ejecuta `python manage.py sincronizar_usuarios_ivs` para realizar la importación inicial.

Las migraciones y la recopilación de estáticos se ejecutan al iniciar `web`. Conserva el volumen y las credenciales de PostgreSQL entre despliegues; cambiar las variables de inicialización no cambia la contraseña de una base ya creada. El contenedor confía en las cabeceras del proxy: no publiques su puerto directamente en producción, y usa un proxy confiable que las sobrescriba.

## WebSockets y archivos

La configuración ASGI incluye autenticación por sesión y validación de origen. Agrega consumidores y rutas a `websocket_urlpatterns` en `inet_ivs/asgi.py` cuando se definan las funciones de tiempo real; no hay endpoints WebSocket todavía.

WhiteNoise sirve los archivos estáticos de Django. Los archivos subidos por usuarios necesitarán almacenamiento persistente separado antes de implementar cargas de archivos.
