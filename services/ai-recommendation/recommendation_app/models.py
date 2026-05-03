import uuid
from django.db import models


class UserBehavior(models.Model):
    """
    User behavior tracking model for AI pipeline
    Tracks: 8 core actions for recommendation and Neo4j graph
    """
    ACTION_CHOICES = [
        ('view_product', 'Xem sản phẩm'),
        ('click_product', 'Click sản phẩm'),
        ('add_to_cart', 'Thêm giỏ hàng'),
        ('remove_from_cart', 'Xóa khỏi giỏ hàng'),
        ('purchase', 'Mua hàng'),
        ('add_to_wishlist', 'Thêm yêu thích'),
        ('search', 'Tìm kiếm'),
        ('view_category', 'Xem danh mục'),
        # Legacy support
        ('view', 'Xem (cũ)'),
        ('cart', 'Giỏ hàng (cũ)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True, verbose_name='ID người dùng')
    product_id = models.UUIDField(db_index=True, null=True, blank=True, verbose_name='ID sản phẩm')
    category_id = models.UUIDField(db_index=True, null=True, blank=True, verbose_name='ID danh mục')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    search_query = models.CharField(max_length=500, blank=True, null=True, verbose_name='Từ khóa tìm kiếm')
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Metadata')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Thời gian')

    class Meta:
        db_table = 'user_behaviors'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'action']),
            models.Index(fields=['product_id', 'action']),
            models.Index(fields=['category_id', 'action']),
            models.Index(fields=['user_id', 'product_id']),
            models.Index(fields=['user_id', 'category_id']),
            models.Index(fields=['user_id', 'created_at']),
        ]
        verbose_name = 'Hành vi người dùng'
        verbose_name_plural = 'Hành vi người dùng'

    def __str__(self):
        target = f"Product {self.product_id}" if self.product_id else f"Category {self.category_id}" if self.category_id else "N/A"
        return f"User {self.user_id} - {self.action} - {target}"

    def to_neo4j_format(self):
        """Format for Neo4j graph import"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'product_id': str(self.product_id) if self.product_id else None,
            'category_id': str(self.category_id) if self.category_id else None,
            'action': self.action,
            'search_query': self.search_query,
            'metadata': self.metadata,
            'timestamp': self.created_at.isoformat(),
        }


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
