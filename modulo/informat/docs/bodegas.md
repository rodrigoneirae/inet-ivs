# Bodegas de I-NET

La tabla real `dbo.BODEGAS` en SQL Server tiene clave primaria `BodCod` (`int`), nombre `BodNom` (`char(35)`), indicador `BodStkEst` (`char(1)`), sucursal `BodSucCod` (`smallint`) e indicador `BodUbi` (`smallint`). Se consulta mediante `modulo.informat.models.erp.BodegaInet` (`managed=False`, `.using('sqlserver')`); **Django no crea ni migra la tabla externa**. El indicador `BodStkEst` se devuelve sin interpretarlo ni filtrar: en la instalación consultada aparecen `D` y `R`, pero su semántica debe confirmarse con Informat. No se exponen dirección, RUT ni responsable.

`GET /api/v1/informat/bodegas/` devuelve `{"bodegas": [{"codigo":"1", "nombre":"...", "estado_stock":"D", "sucursal_codigo":1, "usa_ubicaciones":0}], "pagina":1, "hay_mas":false}`. Acepta `pagina` (desde 1), `tamano` (1–100) y `busqueda` en el nombre. `codigo` es el **código de negocio de I-NET**, presentado como cadena, no un ID interno de registros Django; no hay rutas por identificador entero. Respuestas: 400 parámetros incorrectos, 401 sin autenticación o token inválido, 403 sesión sin permiso, 429 límite de 120/minuto por token, 503 SQL Server o límite Redis no disponibles.

La página `/inventarios/` accede con permiso `inventario.supervisar_inventario`. Otros usuarios web pueden recibir `informat.consultar_bodegas_inet`. Para otra aplicación, el administrador ejecuta `python manage.py crear_token_bodegas --nombre "Otra aplicación"` en el backend: se muestra una vez el token de **solo lectura** y su UUID público. La app consulta con `Authorization: Bearer <token>`. Para revocarlo: `python manage.py revocar_token_bodegas <uuid>`. Estos tokens no autorizan inventarios ni consultas de precios. No copies tokens en el repositorio ni en URLs; utiliza HTTPS. El backend se apoya en el Redis compartido `api_rate_limit` para el límite por token.

El inventario web valida la bodega elegida contra `BODEGAS` antes de crear el inventario; guarda localmente el código y nombre para preservar el historial aunque cambie el maestro. Si I-NET no responde, la creación devuelve 503, no inventa códigos. Los datos históricos locales no se modifican.

## Referencias observadas (consulta de esquema y conteos, 17-11-2026)

- `BODEGAS`: 10 registros; `BodCod` PK; `BodStkEst`: nueve `D`, uno `R`. Todos los `BodUbi` observados eran `0`.
- `BODUBI` (clave compuesta `BodCod`, `UbiCod`, con `UbiNom` y `UbiEst`): **0 registros**. Por ello no sirve actualmente para precargar ubicaciones del conteo móvil.
- `EXIPRDUB` (`PrdBodCod`, `PrdUbiCod`) y `EXISPU` (`BodCod`, `UbiCod`) relacionan productos, bodegas y ubicaciones: **0 registros** en ambas. No se usan para inferir existencias del inventario físico.
- `EXIINV1` y `EXIINV2` tienen `ExiBodCod`; la segunda también `PrdCod` y `ExiInvCan`. Ambas estaban **vacías**. Son referencias del módulo de inventarios ERP, no el historial local de esta app.
- `USUBOD` (PK `BodCod`, `UsuCod`) y `WSIINTBodegas` (vínculo con `WSIINT`) también estaban **vacías**. No se puede inferir asignación de usuarios de ellas.
- Una búsqueda de columnas con `Bod` o `Ubi` encontró 213 coincidencias en otras tablas. La mayoría no tiene clave foránea declarada hacia `BODEGAS`; el nombre de columna sugiere relación, no garantiza semántica. La API se limita al maestro validado.

Las cantidades describen la instalación inspeccionada, no una regla del ERP: pueden cambiar sin aviso.
