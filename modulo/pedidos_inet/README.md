# Cola compatible de pedidos I-NET

Esta aplicación reproduce el intercambio por base de datos de `apps_satventas`.
No crea un endpoint HTTP ni modifica el envío de AnyMarket.

## Contrato de datos

- `EncPedidoApi`: tabla **`inet_encpedidoapi`**.
- `DetPedidoApi`: tabla **`inet_detpedidoapi`**, FK **`enc_pedido_id`**.
- Se conservan los nombres, tipos y nulabilidad de las columnas históricas,
  incluidos los ID internos enteros. Los enlaces del seguimiento usan un UUID
  público adicional, con valor predeterminado también en PostgreSQL para INSERT SQL.
- Hay una restricción única nueva sobre `(enc_pedido_id, nro_linea)`.
- Los importes históricos siguen siendo FloatField por compatibilidad; la
  validación utiliza Decimal y rechaza valores no finitos y totales inconsistentes.
- No se migran automáticamente datos del proyecto anterior ni se cambian sus tablas.
  La migración crea tablas en la base principal de este proyecto. Si ya existen
  tablas con esos nombres, detenerse y evaluar una migración de adopción antes de aplicar.
- El paquete Python nuevo es `modulo.pedidos_inet.models`; los imports del proyecto
  anterior no se conservan. El contrato compatible es el de las tablas/campos.

El productor debe insertar encabezado y **todos** los detalles dentro de una sola
transacción y hacer COMMIT al terminar. El encabezado debe quedar en `P` solo
cuando esté completo. Una fila sin detalles se marca como error, no se envía.
Si necesita varias transacciones, preparar en `R` y publicar con `P` al finalizar.
No insertar más líneas ni modificar un documento una vez publicado.

Un INSERT SQL debe especificar las columnas; los defaults históricos de Django
no se convierten todos en defaults SQL. Las columnas históricas opcionales pueden
ser NULL; el traductor usa los defaults del modelo cuando corresponda. Los campos
nuevos obligatorios sí tienen defaults SQL. No escribir UUID de otros documentos.

Estados: `P` pendiente, `PR` procesando, `E` enviado, `ER` error de validación/rechazo,
`RV` resultado incierto; se conservan `R` y `RS` como estados retenidos no procesables.
El resultado se escribe en `api_documento_*`; los detalles pasan a `E` al confirmar
el documento. Las solicitudes y respuestas se guardan cifradas, sin token SSI,
en `solicitud_cifrada` y `respuesta_cifrada`. Las columnas antiguas `api_json` y
`api_json_response` se conservan pero no se rellenan con datos personales/tokens.
Conservar `DJANGO_SECRET_KEY`: cambiarla impide descifrar la auditoría histórica.

## Activación controlada

1. Revisar la base de destino y aplicar `python manage.py migrate pedidos_inet`.
2. Configurar los tipos de documento autorizados y activar la cola explícitamente:

   ```dotenv
   PEDIDOS_INET_ENABLED=true
   PEDIDOS_INET_DOCUMENTOS_PERMITIDOS=771
   ```

   `771` es un ejemplo, no una autorización preconfigurada. Confirmar los códigos
   reales de la instalación antes de activarlos. Por defecto la cola está apagada
   y ningún tipo está autorizado. Se valida la existencia del cliente con el
   servicio actual de SQL Server antes del envío a Informat.
3. Reiniciar web, worker y la única instancia de Beat. Beat revisa 20 pendientes
   cada 60 segundos. La tarea es `modulo.pedidos_inet.tasks.procesar_pedidos_inet`.
   No necesita invocarse desde el productor.
4. Asignar al personal autorizado el permiso `pedidos_inet.view_encpedidoapi` y
   `pedidos_inet.view_detpedidoapi`. El seguimiento usa el Django Admin existente,
   en **Cola de pedidos I-NET → pedidos I-NET**, con filtros, búsqueda y detalles.
   Es de solo lectura; no se ha añadido una pantalla al dashboard Astro.

La interfaz de documento reproduce Referencias, Cliente, ClienteAdicional,
DescuentosyRecargos, Facturacion, Pedido, Despacho, Detalle y Totales del proyecto
anterior. Se corrige el mapeo antiguo de DYRDesctoUnoPorcentaje/Monto y se respeta
`cliente_referencia` (si no se proporciona, se usa `COLA-<uuid>` estable).
El detalle usa importes netos: su suma debe coincidir con el concepto 100;
el concepto 160 representa el neto final después de descuentos/recargos y su suma
con el IVA (170) debe coincidir con el total (200), con tolerancia de un peso.
Si un documento utiliza otros impuestos o una estructura de cálculo diferente,
adaptar y probar esa validación antes de autorizar su tipo en esta cola.

Ejemplo de publicación con el ORM (los códigos son ilustrativos y deben corresponder
a la configuración real del cliente, producto y documento):

```python
from datetime import date

from django.db import transaction

from modulo.pedidos_inet.models import DetPedidoApi, EncPedidoApi

with transaction.atomic():
    encabezado = EncPedidoApi.objects.create(
        documento_a_generar=771,
        cliente_codigo='12345678', cliente_secuencia=0,
        cliente_referencia='MI-SISTEMA-OC-UNICA',
        fecha_emision=date.today(), fecha_atencion=date.today(),
        bodega_salida='10', vendedor='CODIGO_VENDEDOR', condicion_venta='0',
        concepto_codigo_100=1000, concepto_codigo_160=1000,
        concepto_codigo_170=190, concepto_codigo_200=1190,
        estado_envio='P',
    )
    DetPedidoApi.objects.create(
        enc_pedido=encabezado, nro_linea=1, producto_ventas='SKU_REAL',
        cantidad=2, precio_lista=500, precio_neto=500, total_linea=1000,
    )
```

No ejecutar este ejemplo contra la base real con la cola activa salvo que se quiera
crear efectivamente ese documento. Una aplicación externa puede conservar sus modelos
anteriores apuntando estas tablas a la nueva conexión; debe respetar la transacción,
las validaciones y los estados adicionales descritos arriba.

## Concurrencia y fallos

La reclamación se hace con `select_for_update` y se confirma antes del HTTP.
Una segunda tarea no envía de nuevo el mismo registro. No hay autoretry del envío.
Un procesamiento que permanezca en `PR` más de diez minutos pasa a `RV`, nunca a `P`.
Los registros con número o solicitud previa no se reenvían aunque alguien cambie
su estado a `P`. Ante un resultado incierto, conciliar por referencia en I-NET:
un timeout no significa que el documento no se haya creado. No borrar la auditoría
ni crear una copia del documento para forzar reintentos sin conciliación.

La idempotencia es por registro de cola: el productor sigue siendo responsable de
no insertar dos encabezados para la misma operación de negocio. No se presupone
que Informat deduplique por ClienteReferencia.

Conceder al productor una cuenta PostgreSQL dedicada y privilegios mínimos sobre
estas tablas y sus secuencias; no acceso a usuarios, sesiones ni tablas de otras
aplicaciones. La escritura directa confía en el productor y no usa permisos web.
No utilizar una cuenta de superusuario. No copiar registros reales a pruebas.
