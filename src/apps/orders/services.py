from django.db import transaction
from django.db.models import F

from apps.catalog.models import Product
from apps.orders.models import Order, OrderLog, OrderStatus


class ProductNotFound(Exception):
    pass


class OutOfStock(Exception):
    pass


@transaction.atomic
def purchase_product(*, product_id: int, quantity: int) -> Order:
    """
    1) Atomic decrement stock in DB:
       UPDATE product SET stock = stock - quantity
       WHERE id = product_id AND stock >= quantity

    2) If success -> create Order(status=PENDING) -> OrderLog

    All within a single transaction for consistency.
    """
    if quantity <= 0:
        raise ValueError("quantity must be > 0")

    updated_rows = (
        Product.objects
        .filter(id=product_id, stock__gte=quantity)
        .update(stock=F("stock") - quantity)
    )

    if updated_rows == 0:
        # distinguish: product not found vs out of stock
        if not Product.objects.filter(id=product_id).exists():
            raise ProductNotFound()
        raise OutOfStock()

    order = Order.objects.create(
        product_id=product_id,
        quantity=quantity,
        status=OrderStatus.PENDING,
    )
    OrderLog.objects.create(order=order, event="Order created")

    # enqueue background task (if celery is set)
    try:
        from apps.orders.tasks import process_order
        process_order.delay(order.id)
    except Exception:
        # in early dev phase, if celery is not ready, don't fail the purchase
        # later, when ready, remove this try/except
        pass

    return order