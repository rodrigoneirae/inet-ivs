# Catálogo

El catálogo consulta su maestro local en PostgreSQL. La tarea diaria copia los
campos disponibles de `PRODVENT` en SQL Server; otra tarea importa imágenes y
genera originales y derivados JPEG cuadrados de 1500 y 800 píxeles.

## Entorno

- `CATALOGO_SOURCE_DIR`: dentro de Docker Compose queda fijada a
  `/mnt/catalogo_web`. El host debe montar `//192.168.0.3/catalogo_web` en esa
  ruta. `CATALOGO_HOST_SOURCE_DIR` permite cambiar la ruta del host desde `.env`.
  El volumen SMB se comparte en solo lectura con `web` y `worker`.
- `CATALOGO_STORAGE_ROOT`: en Compose apunta al volumen durable `catalogo_data`,
  compartido entre `web` y `worker`.
- `CATALOGO_TIME_ZONE`: zona horaria de Celery Beat (por defecto
  `America/Santiago`). Las sincronizaciones están programadas a las 03:00 y
  03:30 hora local.

Aplicar las migraciones con `python manage.py migrate catalogo` y mantener
activos el worker Celery y Celery Beat. Si una fuente está caída, el maestro y
los archivos locales ya importados se conservan; las tareas reintentan hasta
tres veces.

En el `.env` de producción, por ejemplo:

```dotenv
CATALOGO_HOST_SOURCE_DIR=/mnt/catalogo_web
CATALOGO_TIME_ZONE=America/Santiago
```

El SMB se monta en el **host Docker**, no dentro del contenedor. Una entrada
`/etc/fstab` típica (la imagen ejecuta la aplicación con UID/GID `10001`) es:

```fstab
//192.168.0.3/catalogo_web /mnt/catalogo_web cifs credentials=/etc/samba/catalogo.credentials,vers=3.0,uid=10001,gid=10001,file_mode=0440,dir_mode=0550,_netdev,nofail,x-systemd.automount 0 0
```

Protege el archivo de credenciales con `root:root` y modo `0600`. Verifica el
montaje en el host antes de iniciar Compose; dentro de los contenedores, la
ruta SMB es de solo lectura y las imágenes procesadas quedan en el volumen
`catalogo_data`.

El código fuente I-NET disponible actualmente solo expone SKU, descripciones,
código de existencia, código de barras y estado. Para filtros por línea,
subclase/familia y atributos técnicos, primero se deben mapear sus campos de
origen.
