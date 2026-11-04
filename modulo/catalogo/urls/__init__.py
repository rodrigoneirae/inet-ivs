from django.urls import path

from modulo.catalogo.views import descargar_imagen, detalle, inicio

app_name = 'catalogo'

urlpatterns = [
    path('', inicio, name='inicio'),
    path('producto/<uuid:public_id>/', detalle, name='detalle'),
    path('producto/<uuid:public_id>/imagen/<int:numero>/<str:tamano>/', descargar_imagen, name='descargar_imagen'),
]
