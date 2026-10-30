"""
URL configuration for inet_ivs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from modulo.acceso import api
from modulo.informat import api as informat_api
from modulo.informat import catalogo as informat_catalogo
from . import views

urlpatterns = [
    path('api/v1/sesion/', api.sesion),
    path('api/v1/informat/stock/', informat_api.stock),
    path('api/v1/informat/token/', informat_api.token_manual),
    path('api/v1/informat/productos/', informat_catalogo.productos),
    path('api/v1/ingresar/', api.ingresar),
    path('api/v1/salir/', api.salir),
    path('api/v1/pedidos/', api.pedidos),
    path('api/v1/pedidos/exportar/', api.exportar),
    path('api/v1/pedidos/sincronizar/', api.sincronizar),
    path('api/v1/pedidos/<uuid:uuid_pedido>/inet/', api.crear_pedido_inet),
    path('api/v1/pedidos/<uuid:uuid_pedido>/inet/errores/', api.errores_pedido_inet),
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('stock/', views.stock, name='stock'),
    path('login/', RedirectView.as_view(url='/', permanent=False), name='login'),
    path('anymarket/', include('modulo.anymarket.urls')),
]
