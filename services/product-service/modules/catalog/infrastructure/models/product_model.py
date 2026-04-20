"""
Product Django ORM Model
Infrastructure layer
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from .category_model import CategoryModel


class ProductModel(models.Model):
    """Django ORM Model cho Product"""

    STATUS_CHOICES = [
        ('draft', 'Nhap'),
        ('active', 'Dang ban'),
        ('inactive', 'Ngung ban'),
        ('out_of_stock', 'Het hang'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Ten san pham')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Mo ta')
    short_description = models.CharField(max_length=500, blank=True, verbose_name='Mo ta ngan')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Ma SKU')
    price = models.DecimalField(
        max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Gia'
    )
    compare_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Gia so sanh'
    )
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Gia von'
    )
    category = models.ForeignKey(
        CategoryModel, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='products', verbose_name='Danh muc'
    )
    brand = models.CharField(max_length=255, blank=True, verbose_name='Thuong hieu')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Trang thai')
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='So luong ton')
    low_stock_threshold = models.IntegerField(default=10, verbose_name='Nguong ton kho thap')
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Can nang (kg)')
    is_featured = models.BooleanField(default=False, verbose_name='Noi bat')
    view_count = models.IntegerField(default=0, verbose_name='Luot xem')
    sold_count = models.IntegerField(default=0, verbose_name='Da ban')
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='Danh gia trung binh')
    rating_count = models.IntegerField(default=0, verbose_name='So luot danh gia')
    seller_id = models.UUIDField(blank=True, null=True, verbose_name='ID nguoi ban')
    attributes = models.JSONField(default=dict, blank=True, verbose_name='Thuoc tinh')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngay tao')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngay cap nhat')

    class Meta:
        db_table = 'products'
        verbose_name = 'San pham'
        verbose_name_plural = 'San pham'
        ordering = ['-created_at']
        app_label = 'catalog'
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['price']),
            models.Index(fields=['-sold_count']),
            models.Index(fields=['-rating_avg']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_on_sale(self):
        return self.compare_price and self.compare_price > self.price

    @property
    def discount_percent(self):
        if self.is_on_sale:
            return int((1 - self.price / self.compare_price) * 100)
        return 0

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold
