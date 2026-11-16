"""Seguimiento de solo lectura en el admin existente, siempre mediante UUID."""

from typing import Any
from uuid import UUID

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, path, reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from .models import DetPedidoApi, EncPedidoApi


class DetalleInline(admin.TabularInline):
    model = DetPedidoApi
    fields = ('nro_linea', 'producto_ventas', 'cantidad', 'precio_neto', 'iva', 'total_linea', 'estado_envio')
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request: HttpRequest, obj: EncPedidoApi | None = None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: EncPedidoApi | None = None) -> bool:
        return False


@admin.register(EncPedidoApi)
class PedidoInetAdmin(admin.ModelAdmin):
    change_form_template = 'admin/pedidos_inet/seguimiento.html'
    list_display = ('ver_pedido', 'estado_envio', 'documento_a_generar', 'nro_orden_compra',
                    'api_documento_numero', 'created_at')
    list_display_links = None
    list_filter = ('estado_envio', 'documento_a_generar')
    search_fields = ('=uuid', 'nro_orden_compra', 'cliente_referencia', 'api_documento_numero')
    list_per_page = 25
    actions = None
    inlines = [DetalleInline]
    fields = ('uuid', 'estado_envio', 'documento_a_generar', 'cliente_referencia', 'nro_orden_compra',
              'cliente_codigo', 'cliente_secuencia', 'fecha_emision', 'bodega_salida', 'vendedor',
              'concepto_codigo_160', 'concepto_codigo_170', 'concepto_codigo_200',
              'api_documento_codigo', 'api_documento_atencion', 'api_documento_numero',
              'api_documento_estado', 'api_documento_error', 'procesando_desde', 'created_at', 'updated_at')
    readonly_fields = fields

    def get_urls(self) -> list[URLPattern]:
        # No registrar rutas heredadas con object_id entero, ni editar/eliminar/reintentar.
        return [
            path('', self.admin_site.admin_view(self.changelist_view), name='pedidos_inet_encpedidoapi_changelist'),
            path('<uuid:object_id>/change/', self.admin_site.admin_view(self.seguimiento),
                 name='pedidos_inet_encpedidoapi_change'),
        ]

    def seguimiento(self, request: HttpRequest, object_id: UUID) -> HttpResponse:
        return self.change_view(request, str(object_id))

    def get_object(self, request: HttpRequest, object_id: str | UUID,
                   from_field: str | None = None) -> EncPedidoApi | None:
        try:
            identificador = UUID(str(object_id))
        except ValueError:
            return None
        return self.get_queryset(request).filter(uuid=identificador).first()

    @admin.display(description='Pedido')
    def ver_pedido(self, obj: EncPedidoApi) -> SafeString:
        url = reverse(f'{self.admin_site.name}:pedidos_inet_encpedidoapi_change', args=[obj.uuid])
        return format_html('<a href="{}">{}</a>', url, obj.uuid)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
