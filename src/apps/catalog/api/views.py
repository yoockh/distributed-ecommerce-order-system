import logging

from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import Product
from apps.catalog.api.serializers import ProductSerializer
from .cache_keys import product_detail_cache_key


logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        responses={
            200: ProductSerializer(many=True),
            400: OpenApiResponse(description="Invalid query params"),
        }
    ),
    retrieve=extend_schema(
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="Product not found"),
        }
    ),
    create=extend_schema(
        responses={
            201: ProductSerializer,
            400: OpenApiResponse(description="Validation error"),
        }
    ),
    update=extend_schema(
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Product not found"),
        }
    ),
    partial_update=extend_schema(
        responses={
            200: ProductSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Product not found"),
        }
    ),
    destroy=extend_schema(
        responses={
            204: OpenApiResponse(description="Product deleted"),
            404: OpenApiResponse(description="Product not found"),
        }
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for Products:
    - GET    /api/products/
    - POST   /api/products/
    - GET    /api/products/{id}/
    - PUT    /api/products/{id}/
    - PATCH  /api/products/{id}/
    - DELETE /api/products/{id}/
    """
    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        raw_pk = kwargs.get(self.lookup_field or "pk")
        if raw_pk is None:
            return super().retrieve(request, *args, **kwargs)

        product_pk = str(raw_pk)
        cache_key = product_detail_cache_key(product_pk)

        try:
            cached = cache.get(cache_key)
        except Exception:  # fallback if Redis misconfigured/unavailable
            logger.warning("Product cache get failed", extra={"product_id": product_pk}, exc_info=True)
            cached = None
        if cached is not None:
            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)
        try:
            cache.set(
                cache_key,
                response.data,
                timeout=settings.PRODUCT_DETAIL_CACHE_TTL,
            )
        except Exception:  # keep serving fresh data if cache disabled
            logger.warning("Product cache set failed", extra={"product_id": product_pk}, exc_info=True)
        return response

    def _invalidate_product_detail_cache(self, product_pk: int | str) -> None:
        try:
            cache.delete(product_detail_cache_key(product_pk))
        except Exception:
            logger.warning(
                "Product cache delete failed",
                extra={"product_id": product_pk},
                exc_info=True,
            )

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_product_detail_cache(instance.pk)

    def perform_destroy(self, instance):
        pk = instance.pk
        super().perform_destroy(instance)
        self._invalidate_product_detail_cache(pk)

