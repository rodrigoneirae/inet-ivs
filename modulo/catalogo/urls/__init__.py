from django.urls import path

from modulo.catalogo.views import descargar_imagenes_producto, detalle_producto, facetas_atributos, imagen, productos

app_name = 'catalogo'

urlpatterns = [
    path('atributos/', facetas_atributos, name='facetas_atributos'),
    path('productos/', productos, name='productos'),
    path('productos/<uuid:public_id>/', detalle_producto, name='detalle_producto'),
    path('productos/<uuid:public_id>/descargar/<str:tamano>/', descargar_imagenes_producto,
         name='descargar_imagenes_producto'),
    path('imagenes/<uuid:public_id>/<int:numero>/<str:tamano>/', imagen, name='imagen'),
]
