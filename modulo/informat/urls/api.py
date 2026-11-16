from django.urls import path

from ..views import catalogo, precios, stock

urlpatterns = [
    path('informat/stock/', stock.stock),
    path('informat/token/', stock.token_manual),
    path('informat/productos/', catalogo.productos),
    path('informat/precios/', precios.precio, name='informat_precio'),
]
