# Referencia de servicios web Informat / I-NET

Resumen de los manuales entregados para preparar la integración. Describe el contrato **documentado**, no una integración probada. Los ejemplos son esquemáticos y utilizan valores ficticios; los campos obligatorios pueden depender de la configuración de I-NET. Los PDF siguen siendo la fuente para el detalle completo y las reglas particulares.

## Fuentes

| Manual | Versión más reciente indicada | Secciones útiles |
| --- | --- | --- |
| [Manual API SSI](Manual%20API%20SSI.pdf) | 1.1, 09-12-2019 | Obtener token, páginas 5 y siguientes |
| [Documentos comerciales](SERVICIO%20WEB%20Documentos%20Comerciales.pdf) | 1.06, 27-10-2022 | Entrada §4.1, ejemplos §4.1.1.1–4.1.1.3, salida §4.2 |
| [Movimientos de existencias](SERVICIO%20WEB%20Movimiento%20Existencias.pdf) | 1.00, 01-08-2022 | Entrada §4.1, ejemplo §4.1.1.1, salida §4.2 |
| [Consulta de productos de ventas](SERVICIOS%20WEB%20Producto%20Ventas%20%28Consulta%29%20%282%29.pdf) | 1.00, 09-02-2022 | Filtros §4.1, salida §4.2 |
| [Recepciones de mercaderías](SERVICIOS%20WEB%20Recepciones%20Mercaderias.pdf) | 1.00, 08-02-2022 | Filtros §4.1, recepción §4.2, salida §4.2.2 |

## Panorama

| Servicio | Ruta documentada | Función | Entrada principal |
| --- | --- | --- | --- |
| SSI | `/AppsSSI/rest/Pssi_ApiGetToken` | Obtener token | `EntradaAut` |
| Productos ventas | `/nombre_aplicacion/rest/wsproductosventas` | Consultar un producto y sus existencias | `ProcesoFiltros` |
| Comercial | `/nombre_aplicacion/rest/wscomercial` | Insertar documentos comerciales | `DocumentoComercial` |
| Existencias | `/nombre_aplicacion/rest/wsexistencias` | Crear movimientos | `MovimientoExistencias` |
| Recepciones | `/nombre_aplicacion/rest/wsrecepciones` | Registrar recepción asociada a guía de traspaso | `ProcesoFiltros` y `Recepcion` |

Los manuales de los cuatro servicios de negocio describen REST y JSON y usan una URL genérica con servidor, puerto y aplicación dependientes de cada instalación. En productos, la captura de la página 15 muestra **POST** con `application/json`; `Accion: "GET"` es un campo del cuerpo. SSI también documenta POST. Confirmar los métodos de los demás servicios, esquema HTTPS y URLs efectivas con Informat.

## Autenticación SSI

El manual identifica `ws.inetcloud.cl`, puerto `8081` y `/AppsSSI/rest/` como datos de referencia, sin establecer un esquema HTTPS. La URL efectiva y el transporte deben confirmarse con el proveedor.

**POST** a `Pssi_ApiGetToken` con JSON:

```json
{
  "EntradaAut": {
    "EmpRut": "<valor cifrado entregado por Informat>",
    "ConId": "<valor cifrado entregado por Informat>",
    "AplId": "<valor cifrado entregado por Informat>",
    "FncId": "<valor cifrado entregado por Informat>"
  }
}
```

- `EmpRut`: RUT de empresa sin dígito verificador; `ConId`: conexión habilitada; `AplId`: aplicación; `FncId`: funcionalidad.
- Informat entrega los cuatro valores cifrados; el consumidor no necesita descifrarlos. El manual cita `IWSINET` y `wscomercial` como ejemplos de aplicación y funcionalidad **antes** de cifrar, no como valores listos para enviar.
- La respuesta contiene `SalidaAut` con `CodigoError`, `Mensaje` y `Token`; el ejemplo de éxito usa `CodigoError: 200`. El manual indica código 402 para cliente no autorizado; no aclara si es un código HTTP o de aplicación.
- El alcance es aplicación y funcionalidad; no se documentan vigencia, renovación ni alcance del token para los demás servicios. Confirmarlos con el proveedor. Mantener valores cifrados y token fuera del código y de los logs.

## Convenciones de respuesta de servicios de negocio

La estructura habitual es `RespuestaProceso`: `Tipo: 0` indica éxito y `Tipo: 1` errores. En éxito, `Datos` es una lista de pares `NOMBRE`/`DATO` que varía por servicio; en error, `Errores` contiene `ErrorCodigo` y `ErrorDescripcion`. No basta con comprobar HTTP: también hay que examinar el resultado de negocio. Algunos ejemplos incluyen `VALOR` adicional.

En comercial, los códigos documentados son 1 (falta de datos), 2 (dato inexistente), 3 (reglas de negocio) y 999 (excepciones). El ejemplo de productos y recepciones incluye un error de token no autorizado dentro de `ErrorDescripcion`. No asumir que la misma clasificación cubre todos los servicios.

## Consulta de productos de ventas

`wsproductosventas` documenta únicamente la acción lógica `GET`. `ProcesoFiltros.Token` es obligatorio; `Filtros` contiene opción `0` con nombres `BODEGA` y `PRODUCTO`. Una bodega vacía consulta todas; el producto debe ser distinto de `0`. Los códigos de producto son cadenas y pueden tener ceros iniciales.

Una integración anterior facilitada por el usuario consulta mediante POST solo con el filtro `BODEGA`, omitiendo `PRODUCTO`, para obtener un listado. Esta posibilidad no está aclarada por el manual; verificar contra la instalación actual y considerar el tamaño de la respuesta.

```json
{
  "ProcesoFiltros": {
    "Token": "<token>",
    "Accion": "GET",
    "Filtros": [
      {"Opcion": 0, "Nombre": "BODEGA", "Dato": "1"},
      {"Opcion": 0, "Nombre": "PRODUCTO", "Dato": "0101019"}
    ]
  }
}
```

Además de `RespuestaProceso`, devuelve `Productos`. La captura de la página 15 muestra una lista de productos con objetos `VENTA` y `EXISTENCIAS`; usa `PRODUCTO_VTA` en vez de `PRODUCTO_VENTA` como indica la tabla. El manual describe también `ATRIBUTOS`, `IMPUESTOS`, `CUENTAS`, `METRICAS`, `COMISIONES`, `PRECIOS`, `STOCK`, `STOCK_BODEGA`, `SERIES_LOTES` y `EXTENSION`. Entre los campos útiles están `PRODUCTO_EXI`, `PRECIO_LISTA`, `STOCK_ACTUAL` y `STOCK_DISPONIBLE`. La captura no muestra el anidamiento del stock: verificarlo con una respuesta real.

## Documentos comerciales

`wscomercial` inserta cotizaciones, pedidos y documentos como facturas, notas de crédito/débito y guías. La entrada se envuelve en `DocumentoComercial`; el token se ubica en `Seguridad.Token`. El manual solo declara la acción insertar y describe estados pendiente/ingresado y emitido/digitado.

Estructura principal:

```text
DocumentoComercial
├── Seguridad.Token
├── Encabezado
│   ├── Referencias.ClienteReferencia
│   ├── Cliente
│   ├── Facturacion
│   └── Despacho, Pedidos, Guia y otras secciones según el caso
├── Detalle.LineasDetalle[]
├── Totales.ConceptosTotales[]
└── Recaudacion.Encabezado / Detalle[]
```

- `ClienteReferencia` es obligatoria, máximo 60 caracteres y debe ser única; el manual indica que se utiliza para detectar referencias existentes. Confirmar el comportamiento ante duplicados y respuestas ambiguas antes de reintentar.
- Cliente: `ClienteCodigo` es el RUT sin dígito verificador ni formato y debe existir en el maestro; `ClienteSecuencia` es obligatorio y su valor por defecto es 0.
- Facturación: `DocumentoOrigen` = 0 documento comercial, 1 cotización, 2 pedido; `DocumentoaGenerar` corresponde al código del maestro. `DocumentoNro` puede ser 0 para pedidos con numeración I-NET. `Estado` = 0 pendiente, 2 emitido. Se documentan como obligatorios moneda, paridad, condición de venta, vendedor, sucursal, lista de precio y fecha de atención. `FechaEmision` no se solicita para pedidos; bodega de salida depende del documento. La paridad de moneda local es 1.
- Debe haber al menos una línea; se marcan `NroLinea`, `ProductoVentas`, `Cantidad`, `PrecioLista` y `TotalLinea` como obligatorios. El producto debe existir en el maestro de ventas. Impuestos, descuentos, series, lotes, ubicaciones y distribución contable dependen del producto y configuración.
- Las listas y secciones no utilizadas pueden representarse como `[]` y `{}` respectivamente según el manual. La recaudación y sus campos se exigen cuando el documento es recaudable.
- En éxito, `Datos` puede contener `DOCUMENTO_CAJA`, `DOCUMENTO_CODIGO`, `DOCUMENTO_ATENCION`, `DOCUMENTO_NUMERO`, `DOCUMENTO_ESTADO`, `DOCUMENTO_ESTADO_DESCRIPCION` y `DOCUMENTO_MOTIVO`.
- Las fechas principales se describen como `AAAA-MM-DD`; para fechas de series/lotes y vencimiento de recaudación se menciona `DD-MM-AAAA`, mientras los ejemplos usan `0000-00-00`. Confirmar el formato y tratamiento de fechas vacías por campo.

## Movimientos de existencias

`wsexistencias` recibe `MovimientoExistencias` con `SEGURIDAD.Token`, `ENCABEZADO` y una lista `DETALLE`. Respetar las mayúsculas de estas claves. El manual marca como obligatorios:

| Sección | Campos | Reglas |
| --- | --- | --- |
| Seguridad | `Token` | Token obtenido de SSI |
| Encabezado | `MovimientoTipo`, `MovimientoCodigo`, `MovimientoEstado`, `MovimientoBodega`, `MovimientoGlosa1`, `MovimientoSistema` | Tipo: 1 entrada, 2 salida, 3 traspaso. Estado: 0 procesado, 2 pendiente. La bodega de salida no puede ser virtual. |
| Detalle | `DetalleSecuencia`, `DetalleProducto`, `DetalleCantidad` | Producto de existencias existente en I-NET. |

`MovimientoBodegaEntrada` es obligatorio para operaciones de traspaso según el tipo de operación y movimiento. Si no se ingresa `MovimientoNumero`, el manual indica que se toma el correlativo disponible; si `MovimientoFechaMovto` está vacío, se usa la fecha del servidor de datos. Las series, lotes, ubicaciones, valores contables y devoluciones dependen de la configuración. Las fechas se describen como `AAAA-MM-DD`.

El éxito devuelve datos identificados como `MOVIMIENTO TIPO`, `MOVIMIENTO CODIGO`, `MOVIMIENTO SUCURSAL`, `MOVIMIENTO NUMERO` y estado. La extracción muestra algunos nombres con posibles erratas, por ejemplo `MovimvientoProveedorSec` en la tabla frente a `MovimientoProveedorSec` en el ejemplo: confirmar antes de enviar.

## Recepciones de mercaderías

`wsrecepciones` registra una recepción asociada a una guía de traspaso existente. El manual presenta **dos parámetros de entrada**, `ProcesoFiltros` y `Recepcion`, por separado; confirmar con el proveedor la envoltura conjunta y el método HTTP.

```json
{
  "ProcesoFiltros": {"Token": "<token>", "Accion": "INS", "Filtros": []},
  "Recepcion": {
    "MOVTO_TIPO": 1,
    "MOVTO_COD": 52,
    "NRO_RECEPCION": 5,
    "NRO_GUIA": 4,
    "FECHA_RECEPCION": "2022-01-31",
    "BODEGA_COD": 30,
    "SUCURSAL_COD": 1,
    "ITEMS": [{"NUMITEM": 1, "PRODUCTO_EXI": "0101019", "CANTIDAD_GUIA": 10, "CANTIDAD_RECEP": 5}]
  }
}
```

El ejemplo anterior combina las dos estructuras mostradas por separado; no se ha verificado que el servidor acepte esa envoltura. `INS` es la única acción documentada y no utiliza filtros. La tabla marca los campos de cabecera y `NUMITEM`, `PRODUCTO_EXI` y cantidad recibida como obligatorios; `CANTIDAD_GUIA` no está marcada obligatoria. `MOVTO_TIPO` es entrada (1); el movimiento debe ser de traspaso y el módulo de adquisiciones debe estar activo y parametrizado. Aunque la tabla marca tipo y código obligatorios, señala que si no tienen valor se toman de los parámetros de adquisiciones: confirmar el comportamiento.

**Inconsistencia:** la tabla llama a la cantidad recibida `CANTIDAD_RECEPCION` (partida por el salto de línea en la extracción), pero el ejemplo usa `CANTIDAD_RECEP`. Confirmar la clave real. La salida se llama `RespuestaProceso` en los ejemplos, aunque algunas secciones la nombran `ProcesoRespuesta`. En éxito, `Datos` incluye tipo, código, sucursal y número de movimiento de la recepción.

## Puntos pendientes para la implementación

1. Solicitar URLs efectivas con HTTPS, método HTTP y cabeceras de cada servicio, credenciales cifradas por funcionalidad y un entorno de pruebas.
2. Confirmar caducidad y renovación del token, códigos de error reales y formato exacto de las respuestas, especialmente `Productos`.
3. Confirmar las discrepancias de nombres, fechas y campos opcionales con Informat; varios ejemplos originales contienen JSON mal formado o claves que difieren de las tablas.
4. Obtener los códigos maestros, reglas comerciales, impuestos y parámetros aplicables a la empresa. Usar aritmética decimal para importes y cantidades.
5. Diseñar tiempos de espera, tratamiento de errores y reconciliación de resultados inciertos para las operaciones de escritura. Una respuesta perdida no demuestra que el servidor no haya creado el registro; no reintentar ciegamente.
