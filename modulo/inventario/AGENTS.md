# AGENTS.md · Módulo de inventario físico

Instrucciones específicas para operar `modulo/inventario/` y la app móvil `inventario_movil/`. Se aplican **además** de las reglas del `AGENTS.md` de la raíz. Si algo aquí contradice a la raíz, prevalece la raíz.

## Qué hace este módulo

Conteo físico de inventario en bodegas de I-NET. Un **supervisor** crea el inventario en la web, asigna **turnos** a **capturadores** (equipos Android) y revisa el análisis A/B. Cada capturador cuenta **sin conexión** y sincroniza **un registro por vez**.

Flujo completo en `modulo/inventario/README.md`. Léelo antes de tocar el módulo.

## Estructura

```
modulo/inventario/
├── models/inventario.py      # Bodega, Zona, Ubicacion, Inventario, Asignacion, Conteo, ProductoSnapshot, TokenMovil
├── forms/inventario.py       # Formularios de validación (ConteoForm, AsignacionForm, PaginaForm…)
├── views/api.py              # API web (sesión + CSRF) y API móvil (Bearer)
├── urls/api.py               # Rutas bajo /api/v1/inventarios/
├── services/analisis.py      # Compara A/B por zona + ubicación + producto
├── services/capturadores.py  # Alta de equipos, huellas de token, vinculación por QR
└── tests/test_inventario.py  # Pruebas del módulo
```

`modulo.inventario` está en `INSTALLED_APPS` y sus rutas bajo `/api/v1/inventarios/`. El frontend vive en `frontend/src/pages/inventarios.astro` y `frontend/src/scripts/inventarios.js`; la app Android en `inventario_movil/`.

## Modelo de dominio

- `Inventario` (bodega, estado `abierto`/`cerrado`) es el contenedor. `creado_por` y `cerrado_por` son usuarios Django.
- `Asignacion` es el **turno**: une inventario, usuario (interno del capturador), tipo `a`/`b`/`unico` y zona o ubicación. Sus restricciones de unicidad (por zona, por ubicación y globales) def qué combinaciones son legales; **no las relajes**.
- `Conteo` usa el **UUID del dispositivo como clave primaria**: es idempotente. Reenviar el mismo evento no duplica ni altera la cantidad.
- `ProductoSnapshot` es una **copia local** del catálogo importado desde `PRODVENT`. El conteo no consulta I-NET en tiempo real.
- `TokenMovil` representa un **capturador**: nombre, token con huella SHA-256, usuario interno asociado, y los datos de vinculación (`vinculacion_hash`, `vinculacion_vence`, `vinculacion_asignacion`, `vinculado_en`).

## Reglas del dominio que no debes romper

1. **La configuración llega del backend.** Bodega, zona, usuario y tipo los define el supervisor en la web al asignar el turno. El operador no escribe la zona. Si necesitas cambiar esto, ajusta backend y app a la vez.
2. **El QR es transporte, no autoridad.** Su código temporal es de un solo uso y vence en 10 minutos. El servidor valida el código y decide la configuración real; nunca confíes en los campos impresos en el QR.
3. **Los tokens se guardan solo como huellas.** Nunca guardes el token en claro en el backend ni lo muestres después de emitirlo. Compara con `secrets.compare_digest`.
4. **Un capturador ve solo lo suyo.** Las rutas móviles filtran por `request.user` (la cuenta interna del equipo). Mantén ese filtro en toda vista que devuelva inventarios, turnos o conteos.
5. **El conteo es idempotente.** Confirma por UUID y borra el evento local solo cuando el servidor confirma ese UUID.
6. **La zona pertenece a la bodega del inventario.** `Asignacion.clean()` valida esa coherencia; los turnos A/B de un inventario deben compartir zona, porque el análisis compara dentro de la misma zona.
7. **No se modifica el stock en I-NET.** El módulo solo lee de `PRODVENT` y `BODEGAS`.

## Autenticación de la API

Dos superficies distintas, no las mezcles:

| Superficie | Credencial | CSRF |
| --- | --- | --- |
| Web `/api/v1/inventarios/…` (salvo `movil/`) | Sesión Django + permiso | Requerido |
| Móvil `/api/v1/inventarios/movil/…` | `Authorization: Bearer <token del equipo>` | Exento (solo token) |
| `POST movil/vincular/` | `Authorization: Bearer <INVENTARIO_APP_TOKEN>` (aplicación) | Exento |

- `_movil()` resuelve el token del equipo y asigna `request.user` y `request.capturador`. **No añadas rutas que ignoren esa resolución.**
- El acceso heredado `Bearer <INVENTARIO_APP_TOKEN>` + `X-Contador` sigue habilitado **solo** para vaciar pendientes de APK anteriores. No lo amplíes; está slated para retirada.
- `INVENTARIO_APP_TOKEN` es un secreto de entorno: aleatorio, mínimo 40 caracteres, nunca en el repositorio.

## Backend y frontend web

- La web usa Astro estático con JavaScript nativo, Tailwind y Tabulator. Sin jQuery, sin `alert()`; los avisos van al elemento `#notification` mediante `toast()`.
- Los QR se generan con el paquete `qrcode` de npm, en el navegador: `QRCode.toCanvas(...)` sobre `#pairing-canvas`.
- Usa `api()` de `frontend/src/scripts/inventarios.js` para las llamadas: adjunta CSRF y normaliza errores.
- **No uses `event.currentTarget` después de un `await`**: el navegador lo deja en `null`. Guarda la referencia antes. Hay una prueba que lo cubre.
- La API web espera JSON; `_datos()` rechaza otro `Content-Type` y cuerpos mayores a 128 KB.

## App móvil (`inventario_movil/`)

- Flutter + SQLite (`sqflite`) + `flutter_secure_storage`. La app guarda inventarios, turnos, catálogo y **eventos pendientes** en SQLite.
- El token del equipo se guarda en almacenamiento seguro, no en SQLite ni en el APK.
- La lista de inventarios se descarga **una sola vez** y persiste, incluso vacía. «Actualizar lista» es manual.
- Cada conteo se guarda primero en SQLite y luego se envía **por separado**; si falla, queda pendiente con su UUID y «Sincronizar pendientes» reintenta todos los inventarios.
- El MC330 lee el QR con su lector 2D integrado mediante DataWedge Intent Output (Broadcast `cl.inversierra.inventario_movil.SCAN`) o Keystroke Output; no usa cámara ni permiso `CAMERA`. En depuración (`kDebugMode`) hay un campo para pegar el contenido.
- Compila con `config/build.local.json` (ignorado por Git). Desde IntelliJ: `--dart-define-from-file=config/build.local.json`. En el emulador, Django se ve en `http://10.0.2.2:8000`, no en `127.0.0.1`.
- No elimines eventos pendientes por la vía de la aplicación: primero sincroniza.

## Verificación

```bash
.venv/bin/python manage.py test modulo.inventario
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
cd frontend && npm run check && npm test
cd inventario_movil && flutter analyze && flutter test
```

Añade pruebas para cada cambio: casos correctos, entradas inválidas, permisos, **aislamiento entre capturadores** y reintentos idempotentes. El módulo no tiene `admin.py`; no lo agregues sin necesidad.

## Migraciones

- **Nunca edites una migración ya aplicada.** Las de `0001`–`0005` ya están aplicadas en la base de desarrollo.
- Las migraciones nuevas solo agregan campos o restricciones; evita cambios con pérdida de datos.
- `TokenMovil.token_hash` es único: al migrar, verifica que no haya hashes repetidos.
- Los datos de I-NET (`BODEGAS`, `PRODVENT`) son **externos**: no los migres ni los administres desde Django. Bodega se copia localmente con su código de negocio, que **no** es un ID interno.
