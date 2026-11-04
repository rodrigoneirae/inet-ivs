from django.urls import path

from ..views import api

urlpatterns = [
    path('acceso/perfiles/usuarios/', api.usuarios_perfiles),
    path('acceso/perfiles/usuario/', api.cambiar_perfil_usuario),
    path('sesion/', api.sesion),
    path('ingresar/', api.ingresar),
    path('salir/', api.salir),
]
