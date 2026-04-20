import uuid
from django.db import models


class DailySales(models.Model):
    """Thống kê doanh số theo ngày"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True, db_index=True)
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    total_items = models.IntegerField(default=0)
    avg_order_value = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    new_customers = models.IntegerField(default=0)
    returning_customers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_sales'
        ordering = ['-date']


class ProductAnalytics(models.Model):
    """Phân tích sản phẩm"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.UUIDField(db_index=True)
    date = models.DateField(db_index=True)
    views = models.IntegerField(default=0)
    add_to_carts = models.IntegerField(default=0)
    purchases = models.IntegerField(default=0)
    revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    conversion_rate = models.FloatField(default=0)

    class Meta:
        db_table = 'product_analytics'
        unique_together = ['product_id', 'date']
        ordering = ['-date']


class CategoryAnalytics(models.Model):
    """Phân tích theo danh mục"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=255, db_index=True)
    date = models.DateField(db_index=True)
    total_views = models.IntegerField(default=0)
    total_sales = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=15, decimal_places=0, default=0)

    class Meta:
        db_table = 'category_analytics'
        unique_together = ['category', 'date']


class SalesPrediction(models.Model):
    """Dự đoán doanh số"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(db_index=True)
    predicted_revenue = models.DecimalField(max_digits=15, decimal_places=0)
    predicted_orders = models.IntegerField()
    confidence = models.FloatField(default=0.8)
    model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales_predictions'
        ordering = ['-date']


class CustomerSegment(models.Model):
    """Phân khúc khách hàng"""
    SEGMENT_CHOICES = [
        ('vip', 'VIP'),
        ('loyal', 'Loyal'),
        ('regular', 'Regular'),
        ('new', 'New'),
        ('at_risk', 'At Risk'),
        ('churned', 'Churned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, db_index=True)
    segment = models.CharField(max_length=20, choices=SEGMENT_CHOICES)
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    avg_order_value = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    days_since_last_order = models.IntegerField(default=0)
    rfm_score = models.FloatField(default=0)  # Recency, Frequency, Monetary
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customer_segments'
