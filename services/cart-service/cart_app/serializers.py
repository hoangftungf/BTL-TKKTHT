from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    variant_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'variant_id', 'product_name', 'product_image', 'price', 'quantity', 'subtotal', 'variant_info']
        read_only_fields = ['id', 'subtotal']

    def get_variant_info(self, obj):
        if not obj.variant_id:
            return None
        try:
            import httpx
            from django.conf import settings
            url = f"{settings.PRODUCT_SERVICE_URL}/{obj.product_id}/"
            response = httpx.get(url, timeout=3.0)
            if response.status_code == 200:
                product = response.json()
                variants = product.get('variants', [])
                variant = next((v for v in variants if str(v.get('id')) == str(obj.variant_id)), None)
                if variant:
                    return {
                        'name': variant.get('name'),
                        'sku': variant.get('sku'),
                        'price': float(variant.get('price')) if variant.get('price') is not None else None,
                        'attributes': variant.get('attributes', {})
                    }
        except Exception:
            pass
        return None


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'items', 'total_items', 'total_amount', 'created_at', 'updated_at']
