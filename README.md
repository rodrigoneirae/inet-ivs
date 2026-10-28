# inet-ivs

Proyecto Django preparado para ASGI, Channels, Celery, Redis y PostgreSQL. Docker Compose ejecuta Django y Channels en `web`, las tareas en `worker`, el planificador en `beat`, PostgreSQL en `db` y Redis en `redis`.

## Desarrollo local sin Docker

Activa el entorno virtual e instala las dependencias:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
uvicorn inet_ivs.asgi:application --host 127.0.0.1 --port 8000 --reload
```

Abre `http://127.0.0.1:8000/admin/`. Para crear un administrador, ejecuta `python manage.py createsuperuser` en otra terminal con `.venv` activado.

Sin variables de PostgreSQL, Django utiliza el archivo local `db.sqlite3`. Redis debe estar ejecutándose en `localhost:6379` para la capa de Channels; comprueba su disponibilidad con `redis-cli ping`. Para utilizar otra dirección, define la variable `REDIS_URL` antes de iniciar Uvicorn. El archivo `.env.dev` corresponde al entorno Docker y no se carga automáticamente en este flujo.

Uvicorn ejecuta ASGI, necesario para WebSockets. Django `runserver` no utiliza el enrutador ASGI de Channels con esta configuración.

### Tailwind CSS sin npm

El tema `theme` usa Tailwind CSS v4 con el ejecutable standalone, sin Node.js ni npm. La primera vez, descarga el ejecutable y genera CSS con:

```bash
python manage.py tailwind install
```

Mientras desarrollas, inicia el observador en otra terminal con `.venv` activado:

```bash
python manage.py tailwind start
```

En PyCharm puedes agregar una configuración **Python** con `manage.py` como script, `tailwind start` como parámetros y la carpeta del proyecto como directorio de trabajo. Agrégala al Compound junto a Uvicorn, Worker y Beat. El observador recompila CSS, pero no recarga el navegador automáticamente.

Extiende `theme/templates/base.html` desde tus plantillas. El CSS generado en `theme/static/css/dist/` se excluye de Git; Docker lo compila durante la construcción de la imagen antes de `collectstatic`. Si usas el Compose local con el código montado, ejecuta `tailwind install` en el equipo primero para generar el CSS local.

Para ejecutar tareas y tareas programadas, abre dos terminales adicionales, activa `.venv` en cada una y ejecuta:

```bash
celery -A inet_ivs worker --loglevel=info
```

```bash
celery -A inet_ivs beat --loglevel=info --schedule=celerybeat-schedule
```

Inicia solo una instancia de Beat para evitar duplicar tareas programadas. El archivo de agenda local está excluido de Git. El worker debe reiniciarse cuando cambia el código de tareas; Beat, cuando cambia su programación.

## Tareas y programación

Define tareas con `@shared_task` en `tasks.py` dentro de una aplicación de Django incluida en `INSTALLED_APPS`. Envíalas con `nombre_de_tarea.delay(...)`. Define la programación en `CELERY_BEAT_SCHEDULE` de `inet_ivs/settings.py`; inicialmente está vacía porque aún no hay tareas de negocio. Para configurar la zona horaria, usa `DJANGO_TIME_ZONE` (por defecto `UTC`).

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

3. Abre `http://localhost:8000/admin/`. Crea un administrador desde otra terminal:

   ```bash
   docker compose --env-file .env.dev -p inet-ivs-dev -f docker-compose.yml -f compose.local.yml exec web python manage.py createsuperuser
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
5. En la terminal del contenedor `web`, ejecuta `python manage.py createsuperuser`.

Las migraciones y la recopilación de estáticos se ejecutan al iniciar `web`. Conserva el volumen y las credenciales de PostgreSQL entre despliegues; cambiar las variables de inicialización no cambia la contraseña de una base ya creada. El contenedor confía en las cabeceras del proxy: no publiques su puerto directamente en producción, y usa un proxy confiable que las sobrescriba.

## WebSockets y archivos

La configuración ASGI incluye autenticación por sesión y validación de origen. Agrega consumidores y rutas a `websocket_urlpatterns` en `inet_ivs/asgi.py` cuando se definan las funciones de tiempo real; no hay endpoints WebSocket todavía.

WhiteNoise sirve los archivos estáticos de Django. Los archivos subidos por usuarios necesitarán almacenamiento persistente separado antes de implementar cargas de archivos.
