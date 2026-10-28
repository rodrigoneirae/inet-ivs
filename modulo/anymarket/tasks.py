from celery import shared_task
from django.db import DatabaseError

from .services import AnyMarketError, sincronizar


@shared_task(ignore_result=True, autoretry_for=(AnyMarketError, DatabaseError),
             retry_backoff=True, retry_kwargs={'max_retries': 3})
def sincronizar_pedidos() -> None:
    sincronizar()
