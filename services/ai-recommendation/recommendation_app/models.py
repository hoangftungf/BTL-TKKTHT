import uuid
from django.db import models


class UserInteraction(models.Model):
    """Lưu trữ tương tác của user với sản phẩm"""
    INTERACTION_TYPES = [
        ('view', 'Xem'),
        ('cart', 'Thêm giỏ hàng'),
        ('purchase', 'Mua'),
        ('wishlist', 'Yêu thích'),
        ('review', 'Đánh giá'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(db_index=True)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    score = models.FloatField(default=1.0)  # Weight của interaction
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_interactions'
        indexes = [
            models.Index(fields=['user_id', 'product_id']),
            models.Index(fields=['product_id', 'interaction_type']),
        ]


class ProductSimilarity(models.Model):
    """Lưu trữ độ tương đồng giữa các sản phẩm (pre-computed)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(db_index=True)
    similar_product_id = models.UUIDField()
    similarity_score = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_similarities'
        unique_together = ['product_id', 'similar_product_id']
        ordering = ['-similarity_score']


class UserRecommendation(models.Model):
    """Lưu trữ recommendations được tính trước cho user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField()
    score = models.FloatField()
    reason = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_recommendations'
        unique_together = ['user_id', 'product_id']
        ordering = ['-score']
