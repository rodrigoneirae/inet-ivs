from django.contrib import admin

from .models import ReglaDocumentoInet


@admin.register(ReglaDocumentoInet)
class ReglaDocumentoInetAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'canal', 'codigo', 'descripcion', 'activa')
    list_filter = ('tipo', 'activa')
    search_fields = ('canal', 'descripcion', 'codigo')
    ordering = ('tipo', 'canal')
