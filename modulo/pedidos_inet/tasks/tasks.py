from celery import shared_task

from ..services import procesar_pendientes


@shared_task(name='modulo.pedidos_inet.tasks.procesar_pedidos_inet', ignore_result=True,
             soft_time_limit=240, time_limit=300)
def procesar_pedidos_inet() -> int:
    # Sin autoretry: una respuesta perdida no garantiza que I-NET no haya creado el pedido.
    return procesar_pendientes()
