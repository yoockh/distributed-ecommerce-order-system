from rest_framework import serializers
from apps.orders.models import Order


class PurchaseRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "product", "quantity", "status", "created_at"]
        read_only_fields = fields