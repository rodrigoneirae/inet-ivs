from celery import shared_task
from django.db import DatabaseError

from modulo.acceso.services import sincronizar_usuarios


@shared_task(name='modulo.acceso.tasks.sincronizar_usuarios_ivs',
             ignore_result=True, autoretry_for=(DatabaseError,), retry_backoff=True,
             retry_kwargs={'max_retries': 3})
def sincronizar_usuarios_ivs() -> None:
    sincronizar_usuarios()
