from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'variant_id', 'product_name', 'product_image', 'price', 'quantity', 'subtotal']
        read_only_fields = ['id', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'items', 'total_items', 'total_amount', 'created_at', 'updated_at']
