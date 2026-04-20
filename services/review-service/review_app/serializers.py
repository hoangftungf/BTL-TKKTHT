from rest_framework import serializers
from .models import Review, ReviewImage, ReviewReply

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'created_at']

class ReviewReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReply
        fields = ['id', 'user_id', 'content', 'is_seller', 'created_at']

class ReviewSerializer(serializers.ModelSerializer):
    images = ReviewImageSerializer(many=True, read_only=True)
    replies = ReviewReplySerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'product_id', 'user_id', 'order_id', 'rating', 'title', 'content',
                  'is_verified', 'helpful_count', 'images', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'is_verified', 'helpful_count', 'created_at', 'updated_at']
