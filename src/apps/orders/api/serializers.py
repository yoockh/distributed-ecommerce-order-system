from rest_framework import serializers
from apps.orders.models import Order, OrderLog


class PurchaseRequestSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class OrderLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderLog
        fields = ["id", "event", "created_at"]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "product", "quantity", "status", "created_at"]
        read_only_fields = fields


class OrderDetailSerializer(OrderListSerializer):
    logs = OrderLogSerializer(many=True, read_only=True)

    class Meta(OrderListSerializer.Meta):
        fields = OrderListSerializer.Meta.fields + ["logs"]
        read_only_fields = fields