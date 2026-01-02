from rest_framework import serializers
from .models import Product, Cart, CartItem, Order


# ======================
# Product Serializer
# ======================
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


# ======================
# Cart Item Serializer
# Shows product NAME instead of product ID
# ======================
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_name",
            "color",
            "size",
            "quantity",
            "total_price",
        ]

    def get_total_price(self, obj):
        return obj.quantity * obj.product.price


# ======================
# Cart Serializer
# Includes cart items
# ======================
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "session_id",
            "items",
        ]


# ======================
# Order Serializer
# Includes full cart details
# ======================
class OrderSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_name",
            "status",
            "cart",
            "payment_screenshot",
            "created_at",
        ]
