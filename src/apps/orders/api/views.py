from typing import Any, cast

from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apps.orders.api.serializers import (
    OrderDetailSerializer,
    OrderListSerializer,
    PurchaseRequestSerializer,
)
from apps.orders.services import OutOfStock, ProductNotFound, purchase_product
from apps.orders.models import Order


@extend_schema_view(
    list=extend_schema(
        responses={
            200: OrderListSerializer(many=True),
            400: OpenApiResponse(description="Invalid filters"),
            500: OpenApiResponse(description="Unexpected server error"),
        }
    ),
    retrieve=extend_schema(
        responses={
            200: OrderDetailSerializer,
            404: OpenApiResponse(description="Order not found"),
            500: OpenApiResponse(description="Unexpected server error"),
        }
    ),
)
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    - GET  /api/orders/        -> list (without logs)
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

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

    @extend_schema(
        request=PurchaseRequestSerializer,
        responses={
            201: OrderListSerializer,
            404: OpenApiResponse(description="Product not found"),
            409: OpenApiResponse(description="Out of stock"),
            422: OpenApiResponse(description="Invalid quantity"),
        },
        description="create order with background processing",
    )
    def create(self, request, *args, **kwargs):
        req = PurchaseRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        validated = cast(dict[str, Any], req.validated_data)
        product_id = cast(int, validated["product_id"])
        quantity = cast(int, validated["quantity"])

        try:
            order = purchase_product(
                product_id=product_id,
                quantity=quantity,
            )
        except ProductNotFound:
            return Response({"detail": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
        except OutOfStock:
            return Response({"detail": "Out of stock"}, status=status.HTTP_409_CONFLICT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        return Response(OrderListSerializer(order).data, status=status.HTTP_201_CREATED)