from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.orders.api.serializers import (
    OrderDetailSerializer,
    OrderListSerializer,
    PurchaseRequestSerializer,
)
from apps.orders.services import OutOfStock, ProductNotFound, purchase_product
from apps.orders.models import Order


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - GET  /api/orders/        -> list (tanpa logs)
    - GET  /api/orders/{id}/   -> detail (with logs)
    - POST /api/orders/        -> purchase
    """
    permission_classes = [AllowAny]
    queryset = Order.objects.all().order_by("-id")

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            return qs.prefetch_related("logs")
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

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

        return Response(OrderListSerializer(order).data, status=status.HTTP_201_CREATED)