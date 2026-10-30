from django.urls import path

from ..views import api

urlpatterns = [
    path('sesion/', api.sesion),
    path('ingresar/', api.ingresar),
    path('salir/', api.salir),
]
