"""
Product Serializers
"""
from rest_framework import serializers
from decimal import Decimal


class ProductListSerializer(serializers.Serializer):
    """Product List Serializer - Hien thi danh sach"""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    slug = serializers.SlugField()
    short_description = serializers.CharField()
    sku = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    compare_price = serializers.SerializerMethodField()
    category_id = serializers.UUIDField(allow_null=True)
    brand = serializers.CharField()
    status = serializers.SerializerMethodField()
    stock_quantity = serializers.IntegerField()
    is_featured = serializers.BooleanField()
    rating_avg = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_count = serializers.IntegerField()
    sold_count = serializers.IntegerField()
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_sku(self, obj):
        return str(obj.sku) if obj.sku else None

    def get_price(self, obj):
        return int(obj.price.amount) if obj.price else 0

    def get_compare_price(self, obj):
        return int(obj.compare_price.amount) if obj.compare_price else None

    def get_status(self, obj):
        return obj.status.value if obj.status else 'draft'


class ProductDetailSerializer(serializers.Serializer):
    """Product Detail Serializer - Hien thi chi tiet"""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    slug = serializers.SlugField()
    description = serializers.CharField()
    short_description = serializers.CharField()
    sku = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    compare_price = serializers.SerializerMethodField()
    cost_price = serializers.SerializerMethodField()
    category_id = serializers.UUIDField(allow_null=True)
    brand = serializers.CharField()
    status = serializers.SerializerMethodField()
    stock_quantity = serializers.IntegerField()
    low_stock_threshold = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    is_featured = serializers.BooleanField()
    view_count = serializers.IntegerField(read_only=True)
    sold_count = serializers.IntegerField(read_only=True)
    rating_avg = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    seller_id = serializers.UUIDField(allow_null=True, read_only=True)
    attributes = serializers.DictField(required=False)
    is_on_sale = serializers.BooleanField(read_only=True)
    discount_percent = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def get_sku(self, obj):
        return str(obj.sku) if obj.sku else None

    def get_price(self, obj):
        return int(obj.price.amount) if obj.price else 0

    def get_compare_price(self, obj):
        return int(obj.compare_price.amount) if obj.compare_price else None

    def get_cost_price(self, obj):
        return int(obj.cost_price.amount) if obj.cost_price else None

    def get_status(self, obj):
        return obj.status.value if obj.status else 'draft'


class ProductCreateSerializer(serializers.Serializer):
    """Product Create Serializer"""

    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)
    sku = serializers.CharField(max_length=100)
    price = serializers.DecimalField(max_digits=12, decimal_places=0, min_value=0)
    category_id = serializers.UUIDField(required=False, allow_null=True)
    brand = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    short_description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    compare_price = serializers.DecimalField(
        max_digits=12, decimal_places=0, min_value=0,
        required=False, allow_null=True
    )
    stock_quantity = serializers.IntegerField(min_value=0, default=0)
    low_stock_threshold = serializers.IntegerField(min_value=0, default=10)
    weight = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    is_featured = serializers.BooleanField(default=False)
    attributes = serializers.DictField(required=False, default=dict)


class ProductUpdateSerializer(serializers.Serializer):
    """Product Update Serializer"""

    name = serializers.CharField(max_length=255, required=False)
    slug = serializers.SlugField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    short_description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    price = serializers.DecimalField(
        max_digits=12, decimal_places=0, min_value=0, required=False
    )
    compare_price = serializers.DecimalField(
        max_digits=12, decimal_places=0, min_value=0,
        required=False, allow_null=True
    )
    category_id = serializers.UUIDField(required=False, allow_null=True)
    brand = serializers.CharField(max_length=255, required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['draft', 'active', 'inactive', 'out_of_stock'],
        required=False
    )
    stock_quantity = serializers.IntegerField(min_value=0, required=False)
    is_featured = serializers.BooleanField(required=False)
    attributes = serializers.DictField(required=False)
