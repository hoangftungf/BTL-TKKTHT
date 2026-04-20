"""
Category Serializers
"""
from rest_framework import serializers


class CategorySerializer(serializers.Serializer):
    """Category Serializer"""

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    image_url = serializers.CharField(read_only=True, allow_null=True)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    is_active = serializers.BooleanField(default=True)
    display_order = serializers.IntegerField(default=0)
    children = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def get_children(self, obj):
        if hasattr(obj, 'children') and obj.children:
            return CategorySerializer(obj.children, many=True).data
        return []
