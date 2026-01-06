from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.catalog.models import Product
from apps.catalog.api.serializers import ProductSerializer


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

