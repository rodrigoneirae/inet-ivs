from django.urls import path

from . import views

app_name = 'anymarket'

urlpatterns = [
    path('pedidos/', views.pedidos, name='pedidos'),
    path('pedidos/exportar/', views.exportar_pedidos, name='exportar_pedidos'),
    path('pedidos/sincronizar/', views.ejecutar_sincronizacion, name='ejecutar_sincronizacion'),
]
