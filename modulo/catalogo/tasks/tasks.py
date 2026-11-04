from celery import shared_task
from django.db import DatabaseError

from modulo.catalogo.services import ErrorSincronizacionCatalogo, sincronizar_imagenes, sincronizar_productos


@shared_task(name='modulo.catalogo.tasks.sincronizar_maestro_catalogo', ignore_result=True,
             autoretry_for=(ErrorSincronizacionCatalogo, DatabaseError), retry_backoff=True,
             retry_kwargs={'max_retries': 3})
def sincronizar_maestro_catalogo() -> int:
    return sincronizar_productos()


@shared_task(name='modulo.catalogo.tasks.sincronizar_imagenes_catalogo', ignore_result=True,
             autoretry_for=(ErrorSincronizacionCatalogo, DatabaseError), retry_backoff=True,
             retry_kwargs={'max_retries': 3})
def sincronizar_imagenes_catalogo() -> int:
    return sincronizar_imagenes()
