import time

from celery import shared_task
from django.db import transaction

from apps.orders.models import Order, OrderLog, OrderStatus


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def process_order(self, order_id: int) -> None:
    # Step 1: mark processing (don't hold transaction during sleep)
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order_id)

        # if already in final state, do nothing
        if order.status in (OrderStatus.COMPLETED, OrderStatus.CANCELLED):
            return

        order.status = OrderStatus.PROCESSING
        order.save(update_fields=["status"])

    # Step 2: simulate external API call
    time.sleep(5)

    # Step 3: mark completed + write log (idempotent)
    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=order_id)

        if order.status == OrderStatus.COMPLETED:
            return
        if order.status == OrderStatus.CANCELLED:
            return

        order.status = OrderStatus.COMPLETED
        order.save(update_fields=["status"])

        OrderLog.objects.create(order=order, event=f"Order #{order.id} Processed.")