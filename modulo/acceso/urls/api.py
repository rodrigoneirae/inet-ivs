from django.urls import path

from ..views import api

urlpatterns = [
    path('sesion/', api.sesion),
    path('ingresar/', api.ingresar),
    path('salir/', api.salir),
    path('pedidos/', api.pedidos),
    path('pedidos/exportar/', api.exportar),
    path('pedidos/sincronizar/', api.sincronizar),
    path('pedidos/<uuid:uuid_pedido>/inet/', api.crear_pedido_inet),
    path('pedidos/<uuid:uuid_pedido>/inet/errores/', api.errores_pedido_inet),
    path('pedidos/<uuid:uuid_pedido>/inet/intentos/<uuid:uuid_intento>/', api.detalle_intento_inet),
]
