import uuid
from django.db import models


class ProductIndex(models.Model):
    """Index sản phẩm cho tìm kiếm nhanh"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(unique=True, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    name_normalized = models.CharField(max_length=255, db_index=True)  # Không dấu
    description = models.TextField(blank=True)
    category = models.CharField(max_length=255, blank=True, db_index=True)
    brand = models.CharField(max_length=255, blank=True, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    keywords = models.TextField(blank=True)  # Extracted keywords
    search_vector = models.TextField(blank=True)  # For full-text search
    popularity_score = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_index'
        indexes = [
            models.Index(fields=['name_normalized']),
            models.Index(fields=['category']),
            models.Index(fields=['brand']),
            models.Index(fields=['-popularity_score']),
        ]


class SearchHistory(models.Model):
    """Lịch sử tìm kiếm để cải thiện autocomplete"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.CharField(max_length=255, db_index=True)
    query_normalized = models.CharField(max_length=255, db_index=True)
    search_count = models.IntegerField(default=1)
    result_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'search_history'
        ordering = ['-search_count']


class Synonym(models.Model):
    """Từ đồng nghĩa cho tìm kiếm"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=100, db_index=True)
    synonyms = models.TextField()  # JSON array
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'synonyms'
