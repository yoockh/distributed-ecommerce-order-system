from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import Product
from apps.catalog.api.serializers import ProductSerializer
from .cache_keys import product_detail_cache_key


class ProductViewSet(viewsets.ModelViewSet):
    """
    CRUD otomatis:
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
        pk = kwargs.get(self.lookup_field or "pk")
        cache_key = product_detail_cache_key(pk)

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(
            cache_key,
            response.data,
            timeout=getattr(settings, "PRODUCT_DETAIL_CACHE_TTL", 300),
        )
        return response

    def _invalidate_product_detail_cache(self, product_pk: int | str) -> None:
        cache.delete(product_detail_cache_key(product_pk))

    def perform_update(self, serializer):
        instance = serializer.save()
        self._invalidate_product_detail_cache(instance.pk)

    def perform_destroy(self, instance):
        pk = instance.pk
        super().perform_destroy(instance)
        self._invalidate_product_detail_cache(pk)

