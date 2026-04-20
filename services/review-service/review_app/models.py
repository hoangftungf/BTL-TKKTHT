import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(verbose_name='ID sản phẩm')
    user_id = models.UUIDField(verbose_name='ID người dùng')
    order_id = models.UUIDField(blank=True, null=True, verbose_name='ID đơn hàng')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Đánh giá')
    title = models.CharField(max_length=255, blank=True, verbose_name='Tiêu đề')
    content = models.TextField(verbose_name='Nội dung')
    is_verified = models.BooleanField(default=False, verbose_name='Đã xác minh mua hàng')
    is_visible = models.BooleanField(default=True, verbose_name='Hiển thị')
    helpful_count = models.IntegerField(default=0, verbose_name='Lượt hữu ích')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        unique_together = ['product_id', 'user_id']

class ReviewImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_images'

class ReviewReply(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='replies')
    user_id = models.UUIDField()
    content = models.TextField()
    is_seller = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_replies'
