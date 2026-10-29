from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'anymarket'

urlpatterns = [
    path('pedidos/', RedirectView.as_view(url='/pedidos/', permanent=False), name='pedidos'),
    path('pedidos/exportar/', views.exportar_pedidos, name='exportar_pedidos'),
    path('pedidos/sincronizar/', views.ejecutar_sincronizacion, name='ejecutar_sincronizacion'),
]
