# inet-ivs

Proyecto Django preparado para ASGI, Django Channels, Redis y PostgreSQL. Docker Compose ejecuta Django y Channels en `web`, PostgreSQL en `db` y Redis en `redis`.

## Prueba local con Docker

1. Copia `.env.example` a `.env` y reemplaza la clave y la contraseña por valores propios. Genera la clave de Django con:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

2. Para probar HTTP localmente, pon `DJANGO_DEBUG=True` en `.env` y levanta los servicios publicando el puerto solo en localhost:

   ```bash
   docker compose -f docker-compose.yml -f compose.local.yml up --build
   ```

3. Abre `http://localhost:8000/admin/`. Crea un administrador desde otra terminal:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

La base se conserva en el volumen `postgres_data`. Redis funciona como canal de mensajes, no como base de datos persistente. La base SQLite local existente no se importa automáticamente a PostgreSQL.

## Dockploy

1. Sube el repositorio a GitHub sin `.env`, SQLite ni el entorno virtual.
2. Crea un servicio **Compose** en Dockploy y conecta el repositorio y la rama. Selecciona `docker-compose.yml`; no incluyas `compose.local.yml`.
3. Configura en las variables del servicio Compose los valores de `.env.example`. Usa una clave y contraseña nuevas, `DJANGO_DEBUG=False`, el dominio en `DJANGO_ALLOWED_HOSTS` y `https://tu-dominio` en `DJANGO_CSRF_TRUSTED_ORIGINS`.
4. Configura el dominio para el servicio `web` y su puerto interno `8000`. Apunta el DNS al servidor y activa HTTPS en Dockploy. Despliega y revisa los logs.
5. En la terminal del contenedor `web`, ejecuta `python manage.py createsuperuser`.

Las migraciones y la recopilación de estáticos se ejecutan al iniciar `web`. Conserva el volumen y las credenciales de PostgreSQL entre despliegues; cambiar las variables de inicialización no cambia la contraseña de una base ya creada. El contenedor confía en las cabeceras del proxy: no publiques su puerto directamente en producción, y usa un proxy confiable que las sobrescriba.

## Desarrollo fuera de Docker

Instala `requirements.txt` en un entorno virtual y ejecuta `python manage.py migrate` y `python manage.py runserver`. Sin `POSTGRES_HOST`, Django utiliza SQLite; para usar Channels con Redis, inicia Redis local en el puerto 6379 o configura `REDIS_URL`.

## WebSockets y archivos

La configuración ASGI incluye autenticación por sesión y validación de origen. Agrega consumidores y rutas a `websocket_urlpatterns` en `inet_ivs/asgi.py` cuando se definan las funciones de tiempo real; no hay endpoints WebSocket todavía.

WhiteNoise sirve los archivos estáticos de Django. Los archivos subidos por usuarios necesitarán almacenamiento persistente separado antes de implementar cargas de archivos.
