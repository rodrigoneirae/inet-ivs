from celery import shared_task
from django.db import DatabaseError

from modulo.anymarket.services import AnyMarketError, reconciliar, sincronizar


@shared_task(name='modulo.anymarket.tasks.sincronizar_pedidos',
             ignore_result=True, autoretry_for=(AnyMarketError, DatabaseError),
             retry_backoff=True, retry_kwargs={'max_retries': 3})
def sincronizar_pedidos() -> None:
    sincronizar()


@shared_task(name='modulo.anymarket.tasks.reconciliar_pedidos',
             ignore_result=True, autoretry_for=(AnyMarketError, DatabaseError),
             retry_backoff=True, retry_kwargs={'max_retries': 3})
def reconciliar_pedidos() -> None:
    reconciliar()
