from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.orders.api.serializers import OrderSerializer, PurchaseRequestSerializer
from apps.orders.services import OutOfStock, ProductNotFound, purchase_product
from apps.orders.models import Order


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - GET /api/orders/        (optional: list)
    - GET /api/orders/{id}/   (optional: retrieve)
    - POST /api/orders/       (purchase)
    """
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        req = PurchaseRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        try:
            order = purchase_product(
                product_id=req.validated_data["product_id"],
                quantity=req.validated_data["quantity"],
            )
        except ProductNotFound:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except OutOfStock:
            return Response({"detail": "Out of stock"}, status=status.HTTP_409_CONFLICT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)