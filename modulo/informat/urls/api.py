from django.urls import path

from ..views import catalogo, stock

urlpatterns = [
    path('informat/stock/', stock.stock),
    path('informat/token/', stock.token_manual),
    path('informat/productos/', catalogo.productos),
]
