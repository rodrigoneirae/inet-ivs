from django.urls import path

from ..views import api

urlpatterns = [
    path('acceso/perfiles/', api.usuarios_perfiles),
    path('acceso/perfiles/usuarios/', api.usuarios_perfiles),
    path('acceso/perfiles/usuario/', api.cambiar_perfil_usuario),
    path('acceso/perfiles/guardar/', api.guardar_perfil),
    path('acceso/perfiles/eliminar/', api.eliminar_perfil),
    path('sesion/', api.sesion),
    path('ingresar/', api.ingresar),
    path('salir/', api.salir),
]
