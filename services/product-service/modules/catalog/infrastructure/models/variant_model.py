"""
Product Variant Django ORM Model
"""
import uuid
from django.db import models

from .product_model import ProductModel


class ProductVariantModel(models.Model):
    """Django ORM Model cho Product Variant"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE,
        related_name='variants', verbose_name='San pham'
    )
    name = models.CharField(max_length=255, verbose_name='Ten bien the')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Ma SKU')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Gia')
    stock_quantity = models.IntegerField(default=0, verbose_name='So luong ton')
    attributes = models.JSONField(default=dict, verbose_name='Thuoc tinh')
    is_active = models.BooleanField(default=True, verbose_name='Hoat dong')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngay tao')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngay cap nhat')

    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Bien the san pham'
        verbose_name_plural = 'Bien the san pham'
        app_label = 'catalog'

    def __str__(self):
        return f"{self.product.name} - {self.name}"
