from django.urls import path

from modulo.inventario.views import api

urlpatterns = [
    path('capturadores/', api.capturadores),
    path('capturadores/crear/', api.crear_dispositivo),
    path('capturadores/<uuid:capturador_id>/qr/', api.generar_qr_dispositivo),
    path('capturadores/<uuid:capturador_id>/revocar/', api.revocar_dispositivo),
    path('capturadores/<uuid:capturador_id>/eliminar/', api.eliminar_dispositivo),
    path('movil/vincular/', api.vincular_dispositivo),
    path('movil/equipo/', api.configuracion_equipo_movil_autorizada),
    path('movil/', api.lista_movil_autorizada),
    path('movil/catalogo/', api.catalogo_movil),
    path('movil/catalogo/importar/', api.importar_catalogo_movil_autorizado),
    path('movil/<uuid:inventario_id>/configuracion/', api.configuracion_movil_autorizada),
    path('movil/asignaciones/<uuid:asignacion_id>/sincronizar/', api.sincronizar_movil),
    path('movil/asignaciones/<uuid:asignacion_id>/finalizar/', api.finalizar_movil),
    path('catalogo/', api.catalogo),
    path('catalogo/importar/', api.importar_productos),
    path('asignaciones/', api.asignaciones),
    path('asignaciones/<uuid:asignacion_id>/sincronizar/', api.sincronizar),
    path('asignaciones/<uuid:asignacion_id>/finalizar/', api.finalizar),
    path('asignaciones/<uuid:asignacion_id>/turno/', api.reconfigurar_turno),
    path('maestros/', api.maestros),
    path('maestros/<str:tipo>/', api.crear_maestro),
    path('', api.inventarios),
    path('crear/', api.crear_inventario),
    path('<uuid:inventario_id>/', api.detalle),
    path('<uuid:inventario_id>/asignar/', api.asignar),
    path('<uuid:inventario_id>/cerrar/', api.cerrar),
]
