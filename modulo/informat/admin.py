from django.contrib import admin

from .models import DispositivoPrecios


@admin.register(DispositivoPrecios)
class DispositivoPreciosAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'public_id', 'lista_codigo', 'activo', 'creado_en')
    list_filter = ('activo', 'lista_codigo')
    search_fields = ('nombre', 'public_id')
    readonly_fields = ('public_id', 'nombre', 'lista_codigo', 'creado_en')
    fields = ('public_id', 'nombre', 'lista_codigo', 'activo', 'creado_en')

    def has_add_permission(self, request: object) -> bool:
        return False  # Emitir el token exclusivamente mediante el comando de provisión.
